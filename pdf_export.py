"""
PDF export module for OPS OKRs Dashboard.

Generates professional PDF reports similar to the reference format.
Uses reportlab for creation.

Usage:
    from pdf_export import generate_okr_pdf

    pdf_bytes = generate_okr_pdf(
        team_name="Payments Team",
        quarter="Q2 2026",
        objectives_df=objectives_df,
        krs_df=krs_df,
        updates_df=updates_df,
        krs_info=krs_info_list,
    )

    # Download in Streamlit:
    st.download_button(
        "Download PDF",
        pdf_bytes,
        file_name=f"OKRs_{team_name}_{quarter}.pdf",
        mime="application/pdf"
    )
"""

import io
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
    KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ─────────────────────────────────────────────────────────
# Colors (matching Ontop brand)
# ─────────────────────────────────────────────────────────

COLOR_PURPLE = colors.HexColor("#7A50F7")
COLOR_PURPLE_DARK = colors.HexColor("#5A30D7")
COLOR_TEAL = colors.HexColor("#2DD4BF")
COLOR_RED = colors.HexColor("#EF4444")
COLOR_YELLOW = colors.HexColor("#FCD34D")
COLOR_GREEN = colors.HexColor("#10B981")
COLOR_DARK_BG = colors.HexColor("#0B0B0F")
COLOR_SURFACE = colors.HexColor("#111118")
COLOR_TEXT = colors.HexColor("#FFFFFF")
COLOR_TEXT_MUTED = colors.HexColor("#B8B8C8")


# ─────────────────────────────────────────────────────────
# Custom styles
# ─────────────────────────────────────────────────────────

def get_custom_styles():
    """Return custom ReportLab styles matching Ontop brand."""
    styles = getSampleStyleSheet()

    # Title
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=COLOR_TEXT,
        spaceAfter=6,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
    ))

    # Subtitle
    styles.add(ParagraphStyle(
        name='CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=COLOR_TEXT_MUTED,
        spaceAfter=12,
        fontName='Helvetica',
    ))

    # Section header
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=COLOR_PURPLE,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
    ))

    # KR title
    styles.add(ParagraphStyle(
        name='KRTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=COLOR_TEXT,
        spaceAfter=4,
        fontName='Helvetica-Bold',
    ))

    # Normal text
    styles.add(ParagraphStyle(
        name='CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=COLOR_TEXT_MUTED,
        spaceAfter=6,
        leading=12,
    ))

    return styles


# ─────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────

def get_status_color(status: str) -> colors.Color:
    """Return color based on status."""
    status_lower = str(status).lower().strip()

    if "completed" in status_lower or "maintain" in status_lower:
        return COLOR_GREEN
    elif "in progress" in status_lower:
        return COLOR_TEAL
    elif "blocked" in status_lower:
        return COLOR_RED
    elif "not started" in status_lower:
        return COLOR_YELLOW
    else:
        return COLOR_TEXT_MUTED


def get_progress_bar(percentage: float, width: float = 2.0) -> Table:
    """Create a simple progress bar as a table."""
    pct = min(100, max(0, float(percentage)))
    filled_width = (pct / 100.0) * width

    bar_data = [
        [
            Table([["▓" * int(filled_width * 10)]],
                  style=TableStyle([
                      ('BACKGROUND', (0, 0), (-1, -1), COLOR_GREEN),
                      ('LEFTPADDING', (0, 0), (-1, -1), 0),
                      ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                      ('TOPPADDING', (0, 0), (-1, -1), 2),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                  ])),
            f"{pct:.0f}%"
        ]
    ]

    return Table(bar_data, colWidths=[1.5*inch, 0.5*inch])


# ─────────────────────────────────────────────────────────
# PDF Generation
# ─────────────────────────────────────────────────────────

def generate_okr_pdf(
    team_name: str,
    quarter: str,
    objectives_df: pd.DataFrame,
    krs_df: pd.DataFrame,
    updates_df: pd.DataFrame,
    krs_info: list,
) -> bytes:
    """
    Generate a professional PDF report of OKRs.

    Args:
        team_name: Name of the team (e.g., "Payments Team")
        quarter: Quarter string (e.g., "Q2 2026")
        objectives_df: DataFrame with objectives
        krs_df: DataFrame with key results
        updates_df: DataFrame with updates
        krs_info: List of KR info dicts with progress data

    Returns:
        PDF as bytes (ready to download)
    """

    # Create PDF in memory
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )

    styles = get_custom_styles()
    story = []

    # ─────────────────────────────────────────────────────────
    # HEADER
    # ─────────────────────────────────────────────────────────

    story.append(Paragraph(f"{team_name}", styles['CustomTitle']))
    story.append(Paragraph(f"{quarter} OKR Progress Dashboard", styles['CustomSubtitle']))
    story.append(Spacer(1, 0.2*inch))

    # Generated date
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y')}",
        styles['CustomNormal']
    ))
    story.append(Spacer(1, 0.3*inch))

    # ─────────────────────────────────────────────────────────
    # KPI CARDS
    # ─────────────────────────────────────────────────────────

    num_objs = len(objectives_df)
    num_krs = len(krs_df)

    # Calculate metrics
    if krs_info:
        avg_progress = sum(k["pct"] for k in krs_info) / len(krs_info) if krs_info else 0
        on_track = sum(1 for k in krs_info if k["pct"] >= 50)
        at_risk = sum(1 for k in krs_info if k["pct"] < 50)
    else:
        avg_progress = 0
        on_track = 0
        at_risk = 0

    kpi_data = [
        ["Objectives", str(num_objs)],
        ["Key Results", str(num_krs)],
        ["Avg Progress", f"{avg_progress:.0f}%"],
        ["On Track", str(on_track)],
        ["At Risk", str(at_risk)],
    ]

    kpi_table = Table(kpi_data, colWidths=[2.5*inch, 1.5*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_SURFACE),
        ('TEXTCOLOR', (0, 0), (-1, -1), COLOR_TEXT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, COLOR_PURPLE),
    ]))

    story.append(kpi_table)
    story.append(Spacer(1, 0.3*inch))

    # ─────────────────────────────────────────────────────────
    # OBJECTIVES & KEY RESULTS TABLE
    # ─────────────────────────────────────────────────────────

    story.append(Paragraph("Key Results Summary", styles['SectionHeader']))

    table_data = [
        ["Objective", "Key Result", "Target", "Current", "Progress", "Status"]
    ]

    if not krs_df.empty and krs_info:
        for kr_info in krs_info:
            kr = kr_info.get("kr", {})

            obj_title = objectives_df[
                objectives_df["id"] == kr.get("objective_id", "")
            ]["title"].values
            obj_title = str(obj_title[0][:40]) if len(obj_title) > 0 else "—"

            kr_title = str(kr.get("title", ""))[:35]
            target = f"{kr.get('target', 0)} {kr.get('unit', '')}"
            current = f"{kr_info.get('val', 0):.1f}"
            pct = kr_info.get("pct", 0)

            # Status badge
            status = "✓ On Track" if pct >= 50 else "⚠ At Risk"

            table_data.append([
                obj_title,
                kr_title,
                target,
                current,
                f"{pct:.0f}%",
                status,
            ])

    krs_table = Table(
        table_data,
        colWidths=[1.5*inch, 1.8*inch, 0.8*inch, 0.8*inch, 0.7*inch, 1.0*inch]
    )
    krs_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PURPLE),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_TEXT),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

        # Body
        ('BACKGROUND', (0, 1), (-1, -1), COLOR_SURFACE),
        ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_TEXT),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_SURFACE, colors.HexColor("#0D0E1A")]),
        ('GRID', (0, 0), (-1, -1), 1, COLOR_PURPLE),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(krs_table)
    story.append(Spacer(1, 0.3*inch))

    # ─────────────────────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────────────────────

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "Ontop Operations OKRs Dashboard",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=COLOR_TEXT_MUTED,
            alignment=TA_CENTER,
        )
    ))

    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)

    return pdf_buffer.getvalue()


# ─────────────────────────────────────────────────────────
# Streamlit helper
# ─────────────────────────────────────────────────────────

def add_pdf_download_button(team_name: str, quarter: str, objectives_df, krs_df, updates_df, krs_info):
    """
    Add a download button to Streamlit for PDF export.

    Usage in app.py:
        from pdf_export import add_pdf_download_button

        with st.container():
            add_pdf_download_button(team_name, quarter, objectives_df, krs_df, updates_df, krs_info)
    """
    import streamlit as st

    pdf_bytes = generate_okr_pdf(team_name, quarter, objectives_df, krs_df, updates_df, krs_info)

    st.download_button(
        label="📥 Download PDF",
        data=pdf_bytes,
        file_name=f"OKRs_{team_name}_{quarter}.pdf",
        mime="application/pdf",
        key=f"pdf_download_{team_name}_{quarter}",
        use_container_width=True,
    )
