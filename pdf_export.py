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
COLOR_ORANGE = colors.HexColor("#F59E0B")
COLOR_WHITE = colors.HexColor("#FFFFFF")
COLOR_TEXT_DARK = colors.HexColor("#1F2937")
COLOR_LIGHT_GRAY = colors.HexColor("#F3F4F6")
COLOR_BORDER = colors.HexColor("#E5E7EB")


# ─────────────────────────────────────────────────────────
# Custom styles
# ─────────────────────────────────────────────────────────

def get_custom_styles():
    """Return custom ReportLab styles."""
    styles = getSampleStyleSheet()

    # Title
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=COLOR_TEXT_DARK,
        spaceAfter=4,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
    ))

    # Subtitle
    styles.add(ParagraphStyle(
        name='CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=12,
        fontName='Helvetica',
    ))

    # Section header
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=COLOR_PURPLE,
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold',
    ))

    # Normal text
    styles.add(ParagraphStyle(
        name='CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_TEXT_DARK,
        spaceAfter=6,
        leading=11,
    ))

    return styles


# ─────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────

def get_status_color(pct: float):
    """Return color based on progress percentage."""
    if pct >= 75:
        return COLOR_GREEN
    elif pct >= 50:
        return COLOR_TEAL
    elif pct >= 25:
        return COLOR_YELLOW
    else:
        return COLOR_RED


def truncate_text(text: str, max_len: int = 40) -> str:
    """Truncate text with ellipsis."""
    text = str(text).strip()
    if len(text) > max_len:
        return text[:max_len - 3] + "..."
    return text


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
        team_name: Name of the team
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
        rightMargin=0.6*inch,
        leftMargin=0.6*inch,
        topMargin=0.6*inch,
        bottomMargin=0.5*inch,
    )

    styles = get_custom_styles()
    story = []

    # ─────────────────────────────────────────────────────────
    # HEADER
    # ─────────────────────────────────────────────────────────

    title = team_name if team_name != "All" else "Operations"
    story.append(Paragraph(f"{title}", styles['CustomTitle']))
    story.append(Paragraph(f"{quarter} OKR Progress Dashboard", styles['CustomSubtitle']))
    story.append(Spacer(1, 0.15*inch))

    # Generated date
    gen_date = datetime.now().strftime('%B %d, %Y')
    story.append(Paragraph(f"Generated: {gen_date}", styles['CustomNormal']))
    story.append(Spacer(1, 0.2*inch))

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
        ["Objectives", f"{num_objs}"],
        ["Key Results", f"{num_krs}"],
        ["Avg Progress", f"{avg_progress:.0f}%"],
        ["On Track", f"{on_track}"],
        ["At Risk", f"{at_risk}"],
    ]

    kpi_table = Table(kpi_data, colWidths=[2.5*inch, 1.2*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, -1), COLOR_TEXT_DARK),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, COLOR_BORDER),
    ]))

    story.append(kpi_table)
    story.append(Spacer(1, 0.25*inch))

    # ─────────────────────────────────────────────────────────
    # KEY RESULTS TABLE
    # ─────────────────────────────────────────────────────────

    story.append(Paragraph("Key Results Summary", styles['SectionHeader']))
    story.append(Spacer(1, 0.08*inch))

    # Table header
    table_data = [
        ["Objective", "Key Result", "Target", "Current", "Progress", "Status"]
    ]

    # Add KR rows
    if krs_info:
        for kr_info in krs_info:
            kr = kr_info.get("kr", {})

            # Get objective title
            obj_id = kr.get("objective_id", "")
            if not objectives_df.empty and "id" in objectives_df.columns:
                obj_rows = objectives_df[objectives_df["id"] == obj_id]
                if not obj_rows.empty:
                    obj_title = truncate_text(str(obj_rows.iloc[0]["title"]), 25)
                else:
                    obj_title = "—"
            else:
                obj_title = "—"

            # KR details
            kr_title = truncate_text(str(kr.get("title", "")), 25)
            target = str(kr.get("target", 0))
            unit = str(kr.get("unit", "")).strip()
            if unit and unit.lower() != "none":
                target = f"{target} {unit}"

            current = f"{kr_info.get('val', 0):.0f}"
            pct = kr_info.get("pct", 0)

            # Status
            status = "✓ On Track" if pct >= 50 else "⚠ At Risk"

            table_data.append([
                obj_title,
                kr_title,
                target,
                current,
                f"{pct:.0f}%",
                status,
            ])
    else:
        table_data.append(["No data available", "", "", "", "", ""])

    # Create table with better proportions
    krs_table = Table(
        table_data,
        colWidths=[1.3*inch, 1.5*inch, 0.85*inch, 0.7*inch, 0.65*inch, 0.85*inch]
    )

    # Table styling - light theme
    krs_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PURPLE),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 0), (1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),

        # Body rows - alternating colors
        ('BACKGROUND', (0, 1), (-1, -1), COLOR_WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_GRAY]),
        ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_TEXT_DARK),
        ('ALIGN', (0, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ]))

    story.append(krs_table)

    # ─────────────────────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────────────────────

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "Ontop Operations OKRs Dashboard",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor("#9CA3AF"),
            alignment=TA_CENTER,
        )
    ))

    # Build PDF
    try:
        doc.build(story)
    except Exception as e:
        print(f"Error building PDF: {e}")
        return b""

    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
