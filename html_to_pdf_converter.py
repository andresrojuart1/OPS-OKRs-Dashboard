"""
Convert HTML report to PDF using reportlab.
No external dependencies like wkhtmltopdf needed.
"""

import io
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def strip_html_tags(text):
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text)


def html_report_to_pdf(html_content: str) -> bytes:
    """
    Convert beautiful HTML report to PDF using reportlab.
    Extracts data from HTML and recreates it as a styled PDF.

    Args:
        html_content: HTML string from generate_html_report()

    Returns:
        PDF bytes
    """
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
    )

    styles = getSampleStyleSheet()

    # Add custom styles with unique names to avoid conflicts
    styles.add(ParagraphStyle(
        name='OKRTitle',
        fontSize=28,
        textColor=colors.HexColor("#FFFFFF"),
        fontName='Helvetica-Bold',
        spaceAfter=6,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='OKRSubtitle',
        fontSize=11,
        textColor=colors.HexColor("#B8B8C8"),
        fontName='Helvetica',
        spaceAfter=12,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='OKRTeamTitle',
        fontSize=18,
        textColor=colors.HexColor("#7A50F7"),
        fontName='Helvetica-Bold',
        spaceAfter=12,
        spaceBefore=12,
    ))

    styles.add(ParagraphStyle(
        name='OKRObjectiveTitle',
        fontSize=12,
        textColor=colors.HexColor("#FFFFFF"),
        fontName='Helvetica-Bold',
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name='OKRBodyText',
        fontSize=9,
        textColor=colors.HexColor("#B8B8C8"),
        fontName='Helvetica',
        spaceAfter=8,
        alignment=TA_JUSTIFY,
    ))

    story = []

    # Parse title from HTML
    title_match = re.search(r'<h1[^>]*>([^<]+)<\/h1>', html_content)
    title = title_match.group(1) if title_match else "OKR Progress Dashboard"

    story.append(Paragraph(title, styles['OKRTitle']))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("Operations Team", styles['OKRSubtitle']))

    # Add generation date
    gen_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    story.append(Paragraph(f"Generated {gen_date}", styles['OKRSubtitle']))
    story.append(Spacer(1, 0.3*inch))

    # Extract team sections from HTML
    # Look for team-section divs
    team_pattern = r'<div class="team-section">(.*?)<\/div>\s*(?=<div class="footer"|$)'
    team_matches = re.finditer(team_pattern, html_content, re.DOTALL)

    for team_match in team_matches:
        team_section = team_match.group(1)

        # Extract team name
        team_name_match = re.search(r'<h2[^>]*>([^<]+)<\/h2>', team_section)
        if team_name_match:
            team_name = strip_html_tags(team_name_match.group(1))
            story.append(Paragraph(team_name, styles['OKRTeamTitle']))
            story.append(Spacer(1, 0.15*inch))

        # Extract objectives blocks
        obj_pattern = r'<div class="objective-block">(.*?)<\/div>\s*(?=<div class="objective-block"|$)'
        obj_matches = re.finditer(obj_pattern, team_section, re.DOTALL)

        for obj_match in obj_matches:
            obj_block = obj_match.group(1)

            # Extract objective title
            obj_title_match = re.search(r'<div class="objective-title">([^<]+)<\/div>', obj_block)
            if obj_title_match:
                obj_title = obj_title_match.group(1).strip()
                story.append(Paragraph(obj_title, styles['OKRObjectiveTitle']))

            # Extract table data
            table_pattern = r'<table class="kr-table">.*?<tbody>(.*?)<\/tbody>.*?<\/table>'
            table_match = re.search(table_pattern, obj_block, re.DOTALL)

            if table_match:
                tbody = table_match.group(1)
                rows = re.findall(r'<tr>(.*?)<\/tr>', tbody, re.DOTALL)

                table_data = [['KEY RESULT', 'STATUS', 'PROGRESS', 'TARGET']]

                for row in rows:
                    cells = re.findall(r'<td[^>]*>([^<]*(?:<[^>]+>[^<]*)*)<\/td>', row)
                    if len(cells) >= 4:
                        kr_title = strip_html_tags(cells[0]).strip()[:50]
                        status = strip_html_tags(cells[1]).strip()
                        progress = strip_html_tags(cells[2]).strip()
                        target = strip_html_tags(cells[3]).strip()

                        table_data.append([kr_title, status, progress, target])

                if len(table_data) > 1:
                    # Create table
                    kr_table = Table(table_data, colWidths=[2.2*inch, 1.0*inch, 0.9*inch, 1.2*inch])
                    kr_table.setStyle(TableStyle([
                        # Header
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#FFFFFF")),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('TOPPADDING', (0, 0), (-1, 0), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

                        # Body
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#0B0B0F")),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor("#FFFFFF")),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 1), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#2A2A3E")),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#0B0B0F"), colors.HexColor("#111118")]),
                    ]))

                    story.append(kr_table)
                    story.append(Spacer(1, 0.15*inch))

            # Extract narrative
            narrative_match = re.search(r'<div class="narrative">(.*?)<\/div>', obj_block, re.DOTALL)
            if narrative_match:
                narrative = narrative_match.group(1)
                narrative_text = strip_html_tags(narrative).strip()
                if narrative_text and "Context & Updates" in narrative_text:
                    narrative_text = narrative_text.replace("Context & Updates", "").strip()
                    if narrative_text and "No notes" not in narrative_text:
                        story.append(Paragraph(f"<i>{narrative_text}</i>", styles['OKRBodyText']))
                        story.append(Spacer(1, 0.1*inch))

        # Page break between teams
        story.append(PageBreak())

    # Footer
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "Ontop Operations OKRs Dashboard | All data from Google Sheets",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor("#6B7280"),
            alignment=TA_CENTER,
        )
    ))

    # Build PDF
    try:
        doc.build(story)
    except Exception as e:
        print(f"[ERROR] Failed to build PDF: {e}")
        return b""

    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
