"""
Professional PDF export for OPS OKRs Dashboard.
Generates multi-page PDF grouped by team with narratives and detailed KR information.

Similar to the reference format: Q2_OKRs (8).pdf
"""

import io
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
    KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


# Colors
COLOR_DARK_BG = colors.HexColor("#0B0B0F")
COLOR_HEADER_BG = colors.HexColor("#1a1a2e")
COLOR_TEXT_WHITE = colors.HexColor("#FFFFFF")
COLOR_TEXT_GRAY = colors.HexColor("#B8B8C8")
COLOR_ACCENT = colors.HexColor("#7A50F7")
COLOR_BORDER = colors.HexColor("#2A2A3E")
COLOR_ON_TRACK = colors.HexColor("#10B981")
COLOR_IN_PROGRESS = colors.HexColor("#2DD4BF")
COLOR_AT_RISK = colors.HexColor("#F59E0B")
COLOR_BLOCKED = colors.HexColor("#EF4444")


def get_status_color(status: str) -> colors.Color:
    """Get color based on status."""
    status_lower = str(status).lower()
    if "on track" in status_lower:
        return COLOR_ON_TRACK
    elif "in progress" in status_lower:
        return COLOR_IN_PROGRESS
    elif "at risk" in status_lower:
        return COLOR_AT_RISK
    elif "blocked" in status_lower:
        return COLOR_BLOCKED
    else:
        return COLOR_TEXT_GRAY


def get_styles():
    """Get custom styles for professional PDF."""
    styles = getSampleStyleSheet()

    # Use unique names to avoid conflicts
    styles.add(ParagraphStyle(
        name='ProfMainTitle',
        fontSize=24,
        textColor=COLOR_TEXT_WHITE,
        fontName='Helvetica-Bold',
        spaceAfter=12,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='ProfTeamTitle',
        fontSize=16,
        textColor=COLOR_ACCENT,
        fontName='Helvetica-Bold',
        spaceAfter=12,
        spaceBefore=6,
    ))

    styles.add(ParagraphStyle(
        name='ProfSectionHeader',
        fontSize=11,
        textColor=COLOR_ACCENT,
        fontName='Helvetica-Bold',
        spaceAfter=8,
        spaceBefore=8,
    ))

    styles.add(ParagraphStyle(
        name='ProfBodyText',
        fontSize=9,
        textColor=COLOR_TEXT_GRAY,
        fontName='Helvetica',
        leading=12,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
    ))

    styles.add(ParagraphStyle(
        name='ProfSmallText',
        fontSize=8,
        textColor=COLOR_TEXT_GRAY,
        fontName='Helvetica',
        leading=10,
    ))

    return styles


def generate_professional_pdf(
    objectives_df: pd.DataFrame,
    krs_df: pd.DataFrame,
    updates_df: pd.DataFrame,
    notes_df: pd.DataFrame,
    quarter: str = "Q2 2026",
) -> bytes:
    """
    Generate professional multi-page PDF grouped by team.

    Args:
        objectives_df: Objectives DataFrame
        krs_df: Key Results DataFrame
        updates_df: Updates DataFrame
        notes_df: Weekly notes DataFrame
        quarter: Quarter string

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

    styles = get_styles()
    story = []

    # Title
    story.append(Paragraph(f"{quarter} OKR Progress Dashboard", styles['ProfMainTitle']))
    story.append(Spacer(1, 0.2*inch))

    # Get unique teams
    if objectives_df.empty:
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    teams = objectives_df["sub_team"].unique() if "sub_team" in objectives_df.columns else ["All"]

    # Process each team
    for i, team in enumerate(teams):
        if i > 0:
            story.append(PageBreak())

        # Team section
        team_objs = objectives_df[objectives_df["sub_team"] == team] if "sub_team" in objectives_df.columns else objectives_df

        story.append(Paragraph(team, styles['ProfTeamTitle']))
        story.append(Spacer(1, 0.1*inch))

        # KR Table for this team
        if not team_objs.empty and not krs_df.empty:
            obj_ids = set(team_objs["id"].astype(str).unique())
            team_krs = krs_df[krs_df["objective_id"].astype(str).isin(obj_ids)]

            if not team_krs.empty:
                table_data = [["KEY RESULT", "STATUS", "Q2 2026\nPROGRESS", "TARGET"]]

                for _, kr in team_krs.iterrows():
                    kr_id = str(kr["id"])
                    kr_title = str(kr["title"])[:60]

                    # Get latest update
                    kr_updates = updates_df[updates_df["kr_id"] == kr_id]
                    if not kr_updates.empty:
                        latest = kr_updates.sort_values("updated_at", ascending=False).iloc[0]
                        current = float(latest.get("new_value", 0))
                        target = float(kr.get("target", 0))
                        pct = (current / target * 100) if target > 0 else 0
                    else:
                        current = float(kr.get("current_value", 0))
                        target = float(kr.get("target", 0))
                        pct = (current / target * 100) if target > 0 else 0

                    # Status
                    if pct >= 75:
                        status = "ON TRACK"
                    elif pct >= 50:
                        status = "IN PROGRESS"
                    elif pct > 0:
                        status = "AT RISK"
                    else:
                        status = "BLOCKED"

                    unit = str(kr.get("unit", "")).strip()
                    target_str = f"{target} {unit}".strip() if unit else str(target)

                    table_data.append([
                        kr_title,
                        status,
                        f"{pct:.0f}%",
                        target_str,
                    ])

                # Create table
                kr_table = Table(table_data, colWidths=[2.5*inch, 1.2*inch, 1.0*inch, 1.3*inch])
                kr_table.setStyle(TableStyle([
                    # Header
                    ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER_BG),
                    ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_TEXT_WHITE),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

                    # Body
                    ('BACKGROUND', (0, 1), (-1, -1), COLOR_DARK_BG),
                    ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_TEXT_WHITE),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ]))

                story.append(kr_table)
                story.append(Spacer(1, 0.15*inch))

        # Notes section
        story.append(Paragraph("NARRATIVE", styles['ProfSectionHeader']))

        team_notes = notes_df[notes_df["sub_team"] == team] if not notes_df.empty else pd.DataFrame()
        if not team_notes.empty:
            # Get most recent notes for this quarter
            quarter_notes = team_notes[team_notes["quarter"] == quarter]
            if not quarter_notes.empty:
                # Sort by week number and get latest
                latest_note = quarter_notes.sort_values("week_number", ascending=False).iloc[0]
                note_content = str(latest_note.get("content", ""))
                if note_content:
                    story.append(Paragraph(note_content, styles['ProfBodyText']))
                else:
                    story.append(Paragraph("No notes available.", styles['ProfSmallText']))
            else:
                story.append(Paragraph("No notes available for this quarter.", styles['ProfSmallText']))
        else:
            story.append(Paragraph("No notes available.", styles['ProfSmallText']))

        story.append(Spacer(1, 0.1*inch))

    # Footer
    story.append(Spacer(1, 0.3*inch))
    gen_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    story.append(Paragraph(
        f"Generated: {gen_date} | Ontop Operations Dashboard",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=7,
            textColor=COLOR_TEXT_GRAY,
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
