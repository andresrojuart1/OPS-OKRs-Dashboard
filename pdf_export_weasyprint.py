"""
Professional PDF export using HTML + Jinja2 + WeasyPrint.
Generates PDFs with full design control, matching the reference format.
"""

import io
from datetime import datetime
import pandas as pd
from jinja2 import Template
from weasyprint import HTML, CSS


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        @page {
            size: letter;
            margin: 0.5in;
        }

        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            background: #0b0f2a;
            color: #ffffff;
            line-height: 1.6;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #7a50f7;
            padding-bottom: 20px;
        }

        .header h1 {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .header p {
            font-size: 12px;
            color: #b8b8c8;
        }

        .team-section {
            margin-bottom: 40px;
            page-break-inside: avoid;
        }

        .team-title {
            font-size: 16px;
            font-weight: bold;
            color: #7a50f7;
            margin-bottom: 15px;
            border-left: 4px solid #7a50f7;
            padding-left: 10px;
        }

        .objectives-group {
            margin-bottom: 25px;
            background: #111118;
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid #7a50f7;
        }

        .objective-title {
            font-size: 13px;
            font-weight: bold;
            color: #ffffff;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .objective-description {
            font-size: 11px;
            color: #b8b8c8;
            margin-bottom: 12px;
            line-height: 1.4;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 11px;
        }

        table thead {
            background: #1a1a2e;
        }

        table th {
            padding: 10px;
            text-align: left;
            font-weight: bold;
            color: #b8b8c8;
            border-bottom: 1px solid #2a2a3e;
            font-size: 10px;
            text-transform: uppercase;
        }

        table td {
            padding: 8px 10px;
            border-bottom: 1px solid #2a2a3e;
            color: #ffffff;
        }

        table tr:nth-child(even) {
            background: #0b0e1a;
        }

        .kr-title {
            font-weight: 500;
            color: #ffffff;
        }

        .status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
            text-align: center;
            min-width: 80px;
        }

        .status.on-track {
            background: #10b981;
            color: #ffffff;
        }

        .status.in-progress {
            background: #2dd4bf;
            color: #0b0f2a;
        }

        .status.at-risk {
            background: #f59e0b;
            color: #0b0f2a;
        }

        .status.blocked {
            background: #ef4444;
            color: #ffffff;
        }

        .status.maintain {
            background: #10b981;
            color: #ffffff;
        }

        .status.not-started {
            background: #6b7280;
            color: #ffffff;
        }

        .progress-cell {
            text-align: center;
        }

        .progress-bar {
            height: 6px;
            background: #2a2a3e;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 4px;
        }

        .progress-fill {
            height: 100%;
            background: #7a50f7;
            transition: width 0.3s ease;
        }

        .target-cell {
            text-align: right;
            color: #b8b8c8;
        }

        .narrative {
            margin-top: 15px;
            padding: 12px;
            background: #0b0e1a;
            border-left: 3px solid #7a50f7;
            border-radius: 4px;
            font-size: 10px;
            color: #b8b8c8;
            line-height: 1.5;
        }

        .narrative-title {
            font-size: 11px;
            font-weight: bold;
            color: #7a50f7;
            margin-bottom: 8px;
            text-transform: uppercase;
        }

        .no-notes {
            color: #6b7280;
            font-style: italic;
        }

        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #2a2a3e;
            text-align: center;
            font-size: 9px;
            color: #6b7280;
        }

        .metrics {
            display: table;
            width: 100%;
            margin-bottom: 30px;
            font-size: 11px;
        }

        .metric {
            display: table-cell;
            padding: 10px;
            background: #111118;
            border: 1px solid #2a2a3e;
            text-align: center;
        }

        .metric-value {
            font-size: 18px;
            font-weight: bold;
            color: #7a50f7;
        }

        .metric-label {
            font-size: 10px;
            color: #b8b8c8;
            margin-top: 5px;
        }

        @media print {
            body {
                background: white;
                color: black;
            }
            .team-section {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>

<div class="header">
    <h1>{{ title }}</h1>
    <p>Generated: {{ generated_date }}</p>
</div>

{% for team_name, team_data in teams.items() %}
<div class="team-section">
    <div class="team-title">{{ team_name }}</div>

    {% if team_data.metrics %}
    <div class="metrics">
        {% for metric in team_data.metrics %}
        <div class="metric">
            <div class="metric-value">{{ metric.value }}</div>
            <div class="metric-label">{{ metric.label }}</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% for obj in team_data.objectives %}
    <div class="objectives-group">
        <div class="objective-title">{{ obj.title }}</div>
        {% if obj.description %}
        <div class="objective-description">{{ obj.description }}</div>
        {% endif %}

        <table>
            <thead>
                <tr>
                    <th>KEY RESULT</th>
                    <th>STATUS</th>
                    <th>PROGRESS</th>
                    <th>TARGET</th>
                </tr>
            </thead>
            <tbody>
                {% for kr in obj.krs %}
                <tr>
                    <td class="kr-title">{{ kr.title }}</td>
                    <td>
                        <span class="status {{ kr.status_class }}">
                            {{ kr.status }}
                        </span>
                    </td>
                    <td class="progress-cell">
                        <div>{{ kr.progress }}%</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {{ kr.progress }}%"></div>
                        </div>
                    </td>
                    <td class="target-cell">{{ kr.target }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        {% if obj.narrative %}
        <div class="narrative">
            <div class="narrative-title">Context</div>
            {{ obj.narrative }}
        </div>
        {% endif %}
    </div>
    {% endfor %}
</div>
{% endfor %}

<div class="footer">
    Ontop Operations OKRs Dashboard | All data from Google Sheets
</div>

</body>
</html>
"""


def generate_weasyprint_pdf(
    objectives_df: pd.DataFrame,
    krs_df: pd.DataFrame,
    updates_df: pd.DataFrame,
    notes_df: pd.DataFrame,
    quarter: str = "Q2 2026",
) -> bytes:
    """
    Generate professional PDF using HTML + Jinja2 + WeasyPrint.

    Args:
        objectives_df: Objectives DataFrame
        krs_df: Key Results DataFrame
        updates_df: Updates DataFrame
        notes_df: Weekly notes DataFrame
        quarter: Quarter string

    Returns:
        PDF bytes
    """

    # Build data structure for template
    teams_data = {}

    if objectives_df.empty or krs_df.empty:
        pdf_html = Template(HTML_TEMPLATE).render(
            title=f"{quarter} OKR Progress Dashboard",
            teams={},
            generated_date=datetime.now().strftime("%B %d, %Y"),
        )
        return HTML(string=pdf_html).write_pdf()

    # Get unique teams
    for team in objectives_df["sub_team"].unique():
        team_objs = objectives_df[objectives_df["sub_team"] == team]
        obj_ids = set(team_objs["id"].astype(str).unique())
        team_krs = krs_df[krs_df["objective_id"].astype(str).isin(obj_ids)]

        objectives_list = []

        for _, obj in team_objs.iterrows():
            obj_id = str(obj["id"])
            obj_krs = team_krs[team_krs["objective_id"] == obj_id]

            krs_list = []
            for _, kr in obj_krs.iterrows():
                kr_id = str(kr["id"])
                kr_title = str(kr["title"])

                # Get latest update
                kr_updates = updates_df[updates_df["kr_id"] == kr_id]
                if not kr_updates.empty:
                    latest = kr_updates.sort_values("updated_at", ascending=False).iloc[0]
                    current = float(latest.get("new_value", 0))
                else:
                    current = float(kr.get("current_value", 0))

                target = float(kr.get("target", 0))
                pct = (current / target * 100) if target > 0 else 0

                # Determine status
                if pct >= 75:
                    status = "ON TRACK"
                    status_class = "on-track"
                elif pct >= 50:
                    status = "IN PROGRESS"
                    status_class = "in-progress"
                elif pct > 0:
                    status = "AT RISK"
                    status_class = "at-risk"
                else:
                    status = "BLOCKED"
                    status_class = "blocked"

                unit = str(kr.get("unit", "")).strip()
                target_str = f"{target} {unit}".strip() if unit else str(target)

                krs_list.append({
                    "title": kr_title,
                    "status": status,
                    "status_class": status_class,
                    "progress": int(pct),
                    "target": target_str,
                })

            # Get narrative for this objective
            narrative = ""
            if not notes_df.empty:
                obj_notes = notes_df[notes_df["sub_team"] == team]
                if not obj_notes.empty:
                    quarter_notes = obj_notes[obj_notes["quarter"] == quarter]
                    if not quarter_notes.empty:
                        latest_note = quarter_notes.sort_values("week_number", ascending=False).iloc[0]
                        narrative = str(latest_note.get("content", ""))

            objectives_list.append({
                "title": str(obj["title"]),
                "description": "",
                "krs": krs_list,
                "narrative": narrative,
            })

        # Calculate team metrics
        total_krs = len(team_krs)
        on_track = sum(1 for o in objectives_list for kr in o["krs"] if kr["status"] == "ON TRACK")
        at_risk = sum(1 for o in objectives_list for kr in o["krs"] if kr["status"] in ["AT RISK", "BLOCKED"])

        metrics = [
            {"value": len(team_objs), "label": "Objectives"},
            {"value": total_krs, "label": "Key Results"},
            {"value": on_track, "label": "On Track"},
            {"value": at_risk, "label": "At Risk"},
        ]

        teams_data[team] = {
            "objectives": objectives_list,
            "metrics": metrics,
        }

    # Render template
    template = Template(HTML_TEMPLATE)
    html_content = template.render(
        title=f"{quarter} OKR Progress Dashboard",
        teams=teams_data,
        generated_date=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
    )

    # Generate PDF
    try:
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception as e:
        print(f"[ERROR] Failed to generate PDF: {e}")
        return b""
