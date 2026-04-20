"""
Enhanced PDF export module with AI-generated insights.

Generates professional PDF reports matching the reference format.
- Professional dark theme with color-coded status badges
- Progress bars and visual indicators
- AI-generated narrative insights using OpenAI
- Team/Objective grouping

Usage:
    from pdf_export_v2 import generate_okr_pdf_with_ai

    pdf_bytes = generate_okr_pdf_with_ai(
        team_name="Payments Team",
        quarter="Q2 2026",
        objectives_df=objectives_df,
        krs_df=krs_df,
        updates_df=updates_df,
        krs_info=krs_info_list,
        openai_api_key="sk-...",
    )
"""

import io
from datetime import datetime
import pandas as pd
import openai
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
    KeepTogether, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


# ─────────────────────────────────────────────────────────
# Colors (Ontop brand + status colors)
# ─────────────────────────────────────────────────────────

COLOR_BG_DARK = colors.HexColor("#0B0B0F")
COLOR_SURFACE = colors.HexColor("#111118")
COLOR_SURFACE_ALT = colors.HexColor("#16161E")
COLOR_TEXT_WHITE = colors.HexColor("#FFFFFF")
COLOR_TEXT_MUTED = colors.HexColor("#B8B8C8")
COLOR_PURPLE = colors.HexColor("#7A50F7")
COLOR_PURPLE_LIGHT = colors.HexColor("#9F7AEA")
COLOR_TEAL = colors.HexColor("#2DD4BF")
COLOR_RED = colors.HexColor("#EF4444")
COLOR_YELLOW = colors.HexColor("#FCD34D")
COLOR_GREEN = colors.HexColor("#10B981")
COLOR_ORANGE = colors.HexColor("#F59E0B")
COLOR_BORDER = colors.HexColor("#2A2A3E")


def get_status_color(status: str) -> colors.Color:
    """Return color based on status text."""
    status_lower = str(status).lower()
    if "completed" in status_lower or "maintain" in status_lower:
        return COLOR_GREEN
    elif "in progress" in status_lower:
        return COLOR_TEAL
    elif "blocked" in status_lower:
        return COLOR_RED
    elif "not started" in status_lower:
        return COLOR_YELLOW
    else:
        return COLOR_ORANGE


def get_progress_color(pct: float) -> colors.Color:
    """Return color based on progress percentage."""
    pct = float(pct)
    if pct >= 75:
        return COLOR_GREEN
    elif pct >= 50:
        return COLOR_TEAL
    elif pct >= 25:
        return COLOR_YELLOW
    else:
        return COLOR_RED


# ─────────────────────────────────────────────────────────
# Custom Styles
# ─────────────────────────────────────────────────────────

def get_styles():
    """Get custom report styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='Title',
        fontSize=28,
        textColor=COLOR_TEXT_WHITE,
        fontName='Helvetica-Bold',
        spaceAfter=4,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='Subtitle',
        fontSize=13,
        textColor=COLOR_TEXT_MUTED,
        fontName='Helvetica',
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontSize=11,
        textColor=COLOR_PURPLE_LIGHT,
        fontName='Helvetica-Bold',
        spaceAfter=8,
        spaceBefore=6,
    ))

    styles.add(ParagraphStyle(
        name='Normal',
        fontSize=9,
        textColor=COLOR_TEXT_MUTED,
        fontName='Helvetica',
        leading=11,
        spaceAfter=4,
        alignment=TA_JUSTIFY,
    ))

    styles.add(ParagraphStyle(
        name='NoteHeader',
        fontSize=9,
        textColor=COLOR_PURPLE,
        fontName='Helvetica-Bold',
        spaceAfter=4,
    ))

    return styles


# ─────────────────────────────────────────────────────────
# AI Insights Generation
# ─────────────────────────────────────────────────────────

def generate_ai_insights(
    team_name: str,
    krs_info: list,
    api_key: str,
) -> str:
    """
    Generate AI-powered insights about OKR performance.

    Args:
        team_name: Team name
        krs_info: List of KR info dicts
        api_key: OpenAI API key

    Returns:
        Markdown string with insights
    """
    if not krs_info or not api_key:
        return ""

    try:
        client = openai.OpenAI(api_key=api_key)

        # Prepare data for AI
        kr_summary = []
        for kr in krs_info[:8]:  # First 8 KRs only to save tokens
            kr_summary.append(
                f"- {kr.get('title', '')}: {kr.get('pct', 0):.0f}% "
                f"({kr.get('val', 0):.0f}/{kr.get('target', 0)})"
            )

        on_track = sum(1 for k in krs_info if k["pct"] >= 50)
        at_risk = sum(1 for k in krs_info if k["pct"] < 50)
        avg_pct = sum(k["pct"] for k in krs_info) / len(krs_info) if krs_info else 0

        prompt = f"""
You are an operations analyst. Generate a brief (2-3 sentences) executive summary
about the {team_name} Q2 2026 OKR performance.

Key metrics:
- Average Progress: {avg_pct:.0f}%
- On Track: {on_track}/{len(krs_info)}
- At Risk: {at_risk}/{len(krs_info)}

Key Results:
{chr(10).join(kr_summary)}

Provide a concise assessment of overall health and critical areas needing attention.
Keep it professional and actionable.
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[WARNING] Failed to generate AI insights: {e}")
        return ""


# ─────────────────────────────────────────────────────────
# PDF Generation
# ─────────────────────────────────────────────────────────

def generate_okr_pdf_with_ai(
    team_name: str,
    quarter: str,
    objectives_df: pd.DataFrame,
    krs_df: pd.DataFrame,
    updates_df: pd.DataFrame,
    krs_info: list,
    openai_api_key: str = None,
) -> bytes:
    """
    Generate professional OKR PDF with AI insights.

    Args:
        team_name: Team name
        quarter: Quarter (e.g., "Q2 2026")
        objectives_df: Objectives DataFrame
        krs_df: Key Results DataFrame
        updates_df: Updates DataFrame
        krs_info: KR info list
        openai_api_key: OpenAI API key (optional)

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

    # ─────────────────────────────────────────────────────────
    # HEADER
    # ─────────────────────────────────────────────────────────

    title = team_name if team_name != "All" else "Operations"
    story.append(Paragraph(f"{title.upper()}", styles['Title']))
    story.append(Paragraph(f"{quarter} OKR Progress Dashboard", styles['Subtitle']))
    story.append(Spacer(1, 0.15*inch))

    # ─────────────────────────────────────────────────────────
    # KPI METRICS
    # ─────────────────────────────────────────────────────────

    num_objs = len(objectives_df)
    num_krs = len(krs_df)
    avg_progress = sum(k["pct"] for k in krs_info) / len(krs_info) if krs_info else 0
    on_track = sum(1 for k in krs_info if k["pct"] >= 50)
    at_risk = sum(1 for k in krs_info if k["pct"] < 50)

    kpi_data = [
        [
            f"{avg_progress:.0f}%\nAvg Progress",
            f"{num_objs}\nObjectives",
            f"{num_krs}\nKey Results",
            f"{on_track}\nOn Track",
            f"{at_risk}\nAt Risk",
        ]
    ]

    kpi_table = Table(kpi_data, colWidths=[1.0*inch]*5)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_SURFACE),
        ('TEXTCOLOR', (0, 0), (-1, -1), COLOR_TEXT_WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, COLOR_BORDER),
    ]))

    story.append(kpi_table)
    story.append(Spacer(1, 0.15*inch))

    # ─────────────────────────────────────────────────────────
    # KEY RESULTS TABLE
    # ─────────────────────────────────────────────────────────

    table_data = [
        ["KEY RESULT", "STATUS", "PROGRESS", "TARGET"]
    ]

    if krs_info:
        for kr_info in krs_info:
            kr = kr_info.get("kr", {})

            # Get objective
            obj_id = kr.get("objective_id", "")
            if not objectives_df.empty and "id" in objectives_df.columns:
                obj_rows = objectives_df[objectives_df["id"] == obj_id]
                obj_title = str(obj_rows.iloc[0]["title"][:40]) if not obj_rows.empty else "—"
            else:
                obj_title = "—"

            kr_title = str(kr.get("title", ""))[:50]
            target = f"{kr.get('target', 0)} {kr.get('unit', '').strip()}"
            pct = kr_info.get("pct", 0)
            current = kr_info.get("val", 0)

            # Determine status
            if pct >= 75:
                status = "✓ ON TRACK"
            elif pct >= 50:
                status = "◐ IN PROGRESS"
            elif pct >= 25:
                status = "⚠ AT RISK"
            else:
                status = "✗ BLOCKED"

            table_data.append([
                f"{obj_title}\n{kr_title}",
                status,
                f"{pct:.0f}%\n({current:.0f}/{kr.get('target', 0)})",
                target,
            ])

    # Create main table
    main_table = Table(table_data, colWidths=[2.8*inch, 1.2*inch, 1.2*inch, 1.3*inch])
    main_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PURPLE),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_TEXT_WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

        # Body
        ('BACKGROUND', (0, 1), (-1, -1), COLOR_SURFACE),
        ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_TEXT_WHITE),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_SURFACE, COLOR_SURFACE_ALT]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, COLOR_BORDER),
    ]))

    story.append(main_table)
    story.append(Spacer(1, 0.2*inch))

    # ─────────────────────────────────────────────────────────
    # AI INSIGHTS
    # ─────────────────────────────────────────────────────────

    if openai_api_key:
        story.append(Paragraph("EXECUTIVE SUMMARY", styles['SectionTitle']))
        insights = generate_ai_insights(team_name, krs_info, openai_api_key)
        if insights:
            story.append(Paragraph(insights, styles['Normal']))
        story.append(Spacer(1, 0.15*inch))

    # ─────────────────────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────────────────────

    gen_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    story.append(Paragraph(
        f"Generated: {gen_date} | Ontop Operations Dashboard",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=7,
            textColor=COLOR_TEXT_MUTED,
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
