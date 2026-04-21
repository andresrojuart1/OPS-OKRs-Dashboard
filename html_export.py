"""
Professional HTML export for OPS OKRs Dashboard.
Generates a beautiful, interactive HTML report that can be opened in any browser.
Styled with Ontop brand colors and responsive design.
"""

from datetime import datetime
import pandas as pd


def generate_html_report(
    objectives_df: pd.DataFrame,
    krs_df: pd.DataFrame,
    updates_df: pd.DataFrame,
    notes_df: pd.DataFrame,
    quarter: str = "Q2 2026",
    charts_df: pd.DataFrame = None,
) -> str:
    """
    Generate professional HTML report grouped by team.

    Args:
        objectives_df: Objectives DataFrame
        krs_df: Key Results DataFrame
        updates_df: Updates DataFrame
        notes_df: Weekly notes DataFrame
        quarter: Quarter string
        charts_df: Weekly charts DataFrame (optional)

    Returns:
        HTML string
    """
    if charts_df is None:
        charts_df = pd.DataFrame()

    # Start building HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{quarter} OKR Progress Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #0B0B0F 0%, #1A1A2E 100%);
            color: #FFFFFF;
            line-height: 1.6;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 50px;
            padding-bottom: 30px;
            border-bottom: 2px solid #7A50F7;
        }}

        .header h1 {{
            font-size: 42px;
            font-weight: 800;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #FFFFFF, #B8B8C8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .header p {{
            font-size: 14px;
            color: #B8B8C8;
            margin-top: 10px;
        }}

        .team-section {{
            margin-bottom: 60px;
            page-break-inside: avoid;
        }}

        .team-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #7A50F7;
        }}

        .team-header h2 {{
            font-size: 28px;
            font-weight: 700;
            color: #7A50F7;
            margin: 0;
        }}

        .team-badge {{
            display: inline-block;
            background: rgba(122, 80, 247, 0.15);
            color: #7A50F7;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}

        .metrics-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(122, 80, 247, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}

        .metric-value {{
            font-size: 32px;
            font-weight: 800;
            color: #7A50F7;
            margin-bottom: 8px;
        }}

        .metric-label {{
            font-size: 12px;
            color: #B8B8C8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .objectives-container {{
            display: grid;
            gap: 20px;
        }}

        .objective-block {{
            background: #111118;
            border-left: 4px solid #7A50F7;
            border-radius: 8px;
            padding: 24px;
        }}

        .objective-title {{
            font-size: 16px;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .kr-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}

        .kr-table thead {{
            background: rgba(0, 0, 0, 0.3);
        }}

        .kr-table th {{
            padding: 12px 16px;
            text-align: left;
            font-size: 11px;
            font-weight: 700;
            color: #B8B8C8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid #2A2A3E;
        }}

        .kr-table td {{
            padding: 14px 16px;
            border-bottom: 1px solid #2A2A3E;
            font-size: 13px;
            color: #FFFFFF;
        }}

        .kr-table tbody tr:hover {{
            background: rgba(122, 80, 247, 0.05);
        }}

        .kr-title {{
            font-weight: 500;
            color: #FFFFFF;
        }}

        .status-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            text-align: center;
            min-width: 90px;
        }}

        .status-on-track {{
            background: rgba(16, 185, 129, 0.2);
            color: #10B981;
            border: 1px solid #10B981;
        }}

        .status-in-progress {{
            background: rgba(45, 212, 191, 0.2);
            color: #2DD4BF;
            border: 1px solid #2DD4BF;
        }}

        .status-at-risk {{
            background: rgba(245, 158, 11, 0.2);
            color: #F59E0B;
            border: 1px solid #F59E0B;
        }}

        .status-blocked {{
            background: rgba(239, 68, 68, 0.2);
            color: #EF4444;
            border: 1px solid #EF4444;
        }}

        .progress-cell {{
            text-align: center;
        }}

        .progress-bar {{
            width: 100%;
            height: 6px;
            background: #2A2A3E;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 6px;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #7A50F7, #2DD4BF);
            border-radius: 3px;
            transition: width 0.3s ease;
        }}

        .target-cell {{
            text-align: right;
            color: #B8B8C8;
            font-size: 12px;
        }}

        .narrative {{
            background: rgba(255, 255, 255, 0.02);
            border-left: 3px solid #7A50F7;
            border-radius: 6px;
            padding: 16px;
            margin-top: 16px;
            font-size: 13px;
            line-height: 1.7;
        }}

        .narrative-title {{
            font-size: 12px;
            font-weight: 700;
            color: #7A50F7;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 10px;
        }}

        .narrative-text {{
            color: #B8B8C8;
            line-height: 1.6;
        }}

        .no-notes {{
            color: #6B7280;
            font-style: italic;
            font-size: 12px;
        }}

        .charts-section {{
            margin-top: 30px;
            border-top: 2px solid #2A2A3E;
            padding-top: 20px;
        }}

        .charts-title {{
            font-size: 14px;
            font-weight: 700;
            color: #7A50F7;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 16px;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 16px;
        }}

        .chart-image {{
            width: 100%;
            max-width: 500px;
            border-radius: 8px;
            border: 1px solid #2A2A3E;
            background: #111118;
            padding: 8px;
        }}

        .footer {{
            margin-top: 60px;
            padding-top: 30px;
            border-top: 1px solid #2A2A3E;
            text-align: center;
            font-size: 11px;
            color: #6B7280;
        }}

        @media print {{
            body {{
                background: #FFFFFF;
                color: #000000;
            }}
            .team-section {{
                page-break-inside: avoid;
            }}
            .kr-table {{
                page-break-inside: avoid;
            }}
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 28px;
            }}
            .metrics-row {{
                grid-template-columns: 1fr;
            }}
            .kr-table {{
                font-size: 12px;
            }}
            .kr-table th, .kr-table td {{
                padding: 10px 12px;
            }}
        }}
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>{quarter} OKR Progress Dashboard</h1>
        <p>Operations Team</p>
        <p style="margin-top: 16px; font-size: 12px;">Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
"""

    if objectives_df.empty or krs_df.empty:
        html += """
    <div style="text-align: center; padding: 60px 20px; color: #B8B8C8;">
        <p>No data available for this quarter.</p>
    </div>
</body>
</html>
"""
        return html

    # Get unique teams
    teams = sorted(objectives_df["sub_team"].unique()) if "sub_team" in objectives_df.columns else ["All"]

    # Process each team
    for team in teams:
        team_objs = objectives_df[objectives_df["sub_team"] == team] if "sub_team" in objectives_df.columns else objectives_df
        obj_ids = set(team_objs["id"].astype(str).unique())
        team_krs = krs_df[krs_df["objective_id"].astype(str).isin(obj_ids)]

        if team_objs.empty or team_krs.empty:
            continue

        # Calculate metrics
        total_objs = len(team_objs)
        total_krs = len(team_krs)
        on_track = 0
        at_risk = 0

        for _, kr in team_krs.iterrows():
            kr_id = str(kr["id"])
            kr_updates = updates_df[updates_df["kr_id"] == kr_id]
            if not kr_updates.empty:
                latest = kr_updates.sort_values("updated_at", ascending=False).iloc[0]
                current = float(latest.get("new_value", 0))
            else:
                current = float(kr.get("current_value", 0))

            target = float(kr.get("target", 0))
            pct = (current / target * 100) if target > 0 else 0

            if pct >= 75:
                on_track += 1
            elif pct < 50:
                at_risk += 1

        html += f"""
    <div class="team-section">
        <div class="team-header">
            <h2>{team}</h2>
            <span class="team-badge">{total_objs} Objectives</span>
        </div>

        <div class="metrics-row">
            <div class="metric-card">
                <div class="metric-value">{total_objs}</div>
                <div class="metric-label">Objectives</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_krs}</div>
                <div class="metric-label">Key Results</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{on_track}</div>
                <div class="metric-label">On Track</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{at_risk}</div>
                <div class="metric-label">At Risk</div>
            </div>
        </div>

        <div class="objectives-container">
"""

        # Group KRs by objective
        for _, obj in team_objs.iterrows():
            obj_id = str(obj["id"])
            obj_krs = team_krs[team_krs["objective_id"] == obj_id]

            if obj_krs.empty:
                continue

            obj_title = str(obj.get("title", "Untitled"))

            html += f"""
            <div class="objective-block">
                <div class="objective-title">{obj_title}</div>

                <table class="kr-table">
                    <thead>
                        <tr>
                            <th>KEY RESULT</th>
                            <th>STATUS</th>
                            <th>PROGRESS</th>
                            <th>TARGET</th>
                        </tr>
                    </thead>
                    <tbody>
"""

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
                    status_class = "status-on-track"
                elif pct >= 50:
                    status = "IN PROGRESS"
                    status_class = "status-in-progress"
                elif pct > 0:
                    status = "AT RISK"
                    status_class = "status-at-risk"
                else:
                    status = "BLOCKED"
                    status_class = "status-blocked"

                unit = str(kr.get("unit", "")).strip()
                target_str = f"{target} {unit}".strip() if unit else str(target)

                html += f"""
                        <tr>
                            <td class="kr-title">{kr_title}</td>
                            <td><span class="status-badge {status_class}">{status}</span></td>
                            <td class="progress-cell">
                                <div>{pct:.0f}%</div>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {pct:.0f}%"></div>
                                </div>
                            </td>
                            <td class="target-cell">{target_str}</td>
                        </tr>
"""

            html += """
                    </tbody>
                </table>
"""

            # Add narrative
            team_notes = notes_df[notes_df["sub_team"] == team] if not notes_df.empty else pd.DataFrame()
            if not team_notes.empty:
                quarter_notes = team_notes[team_notes["quarter"] == quarter]
                if not quarter_notes.empty:
                    latest_note = quarter_notes.sort_values("week_number", ascending=False).iloc[0]
                    note_content = str(latest_note.get("content", ""))
                    if note_content:
                        html += f"""
                <div class="narrative">
                    <div class="narrative-title">Context & Updates</div>
                    <div class="narrative-text">{note_content}</div>
                </div>
"""
                    else:
                        html += """
                <div class="narrative">
                    <div class="narrative-title">Context & Updates</div>
                    <div class="no-notes">No notes available.</div>
                </div>
"""

            html += """
            </div>
"""

        html += """
        </div>
"""

        # Add charts for this team
        team_charts = charts_df[
            (charts_df["sub_team"] == team) &
            (charts_df["quarter"] == quarter)
        ] if not charts_df.empty else pd.DataFrame()

        if not team_charts.empty:
            html += """
        <div class="charts-section">
            <div class="charts-title">📊 Weekly Charts</div>
            <div class="charts-grid">
"""
            for _, chart in team_charts.iterrows():
                drive_url = str(chart.get("drive_url", "")).strip()
                filename = str(chart.get("filename", "Chart")).strip()
                if drive_url and drive_url.lower() != "nan":
                    html += f"""
                <div>
                    <img src="{drive_url}" alt="{filename}" class="chart-image">
                    <p style="font-size: 12px; color: #B8B8C8; margin-top: 8px; text-align: center;">{filename}</p>
                </div>
"""
            html += """
            </div>
        </div>
"""

        html += """
    </div>
"""

    html += f"""
    <div class="footer">
        <p>Ontop Operations OKRs Dashboard | All data from Google Sheets</p>
        <p style="margin-top: 8px;">This report was automatically generated. For questions or updates, contact the Operations team.</p>
    </div>
</div>

</body>
</html>
"""

    return html
