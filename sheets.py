"""Google Sheets helpers — init, seed, CRUD via gspread + service account."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import gspread
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv(override=True)

_here = os.path.dirname(os.path.abspath(__file__))


def _secret(key: str, default: str = "") -> str:
    """Read from st.secrets (Streamlit Cloud) or os.getenv (local)."""
    try:
        val = st.secrets.get(key)
        if val is not None:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

@st.cache_resource
def get_gspread_client() -> gspread.Client:
    sa_json = _secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    sa_file = os.path.join(_here, _secret("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json"))
    if sa_json:
        creds = Credentials.from_service_account_info(
            json.loads(sa_json), scopes=SCOPES
        )
    elif os.path.isfile(sa_file):
        creds = Credentials.from_service_account_file(sa_file, scopes=SCOPES)
    else:
        raise EnvironmentError(
            "No service account credentials found. Set GOOGLE_SERVICE_ACCOUNT_JSON "
            "or place service_account.json in the project directory."
        )
    return gspread.authorize(creds)


@st.cache_resource
def get_spreadsheet() -> gspread.Spreadsheet:
    return get_gspread_client().open_by_key(_secret("GSPREAD_SPREADSHEET_ID"))


def get_worksheet(name: str) -> gspread.Worksheet:
    return get_spreadsheet().worksheet(name)


def get_service_account_credentials() -> Credentials:
    """Return raw service account credentials for use with other Google APIs."""
    sa_json = _secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    sa_file = os.path.join(_here, _secret("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json"))
    if sa_json:
        return Credentials.from_service_account_info(json.loads(sa_json), scopes=SCOPES)
    elif os.path.isfile(sa_file):
        return Credentials.from_service_account_file(sa_file, scopes=SCOPES)
    raise EnvironmentError("No service account credentials found.")


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

SEED_OBJECTIVES = [
    {
        "id": "O1",
        "title": "Scale Financial Products into Reliable ARR Contributors, Building a Second Revenue Engine Alongside Payroll",
        "sub_team": "New Initiatives",
        "quarter": "Q2 2026",
        "company_vision": "",
    },
    {
        "id": "O2",
        "title": "Close the Margin Gap and Ensure Every Payment Rail Operates at Target Profitability",
        "sub_team": "FinOps",
        "quarter": "Q2 2026",
        "company_vision": "",
    },
    {
        "id": "O3",
        "title": "Eliminate Human Intervention as Default in Support, with AI Resolving Most Volume at High CSAT",
        "sub_team": "AI Experience",
        "quarter": "Q2 2026",
        "company_vision": "",
    },
    {
        "id": "O4",
        "title": "Launch Revenue-Generating AI Products That Create a New Direct Monetization Layer",
        "sub_team": "AI Monetization",
        "quarter": "Q2 2026",
        "company_vision": "",
    },
    {
        "id": "O5",
        "title": "Empower the Entire Ontop Organization with the AI Agentic Workflow Framework to Transform Operational Excellence",
        "sub_team": "AI Monetization",
        "quarter": "Q2 2026",
        "company_vision": "",
    },
    {
        "id": "O6",
        "title": "Achieve ISO 27001 Readiness and Pass Pre-Audit to Unlock Enterprise and Regulated Markets",
        "sub_team": "Security & Compliance Ops",
        "quarter": "Q2 2026",
        "company_vision": "",
    },
]

SEED_KEY_RESULTS = [
    # O1 — New Initiatives
    {"id": "KR1",  "objective_id": "O1", "title": "Revenue from new initiatives reaches $20K/month",                               "target": 20000,   "unit": "$",           "current_value": 0},
    {"id": "KR2",  "objective_id": "O1", "title": "Quick monthly disbursement volume reaches $500K/month",                          "target": 500000,  "unit": "$/month",     "current_value": 0},
    {"id": "KR3",  "objective_id": "O1", "title": "Future Fund AUM reaches $8M between CD and MMF vault",                           "target": 9000000, "unit": "$",           "current_value": 0},
    # O2 — FinOps
    {"id": "KR4",  "objective_id": "O2", "title": "Pay-ins gross margin reaches 20%",                                               "target": 20,      "unit": "%",           "current_value": 0},
    {"id": "KR5",  "objective_id": "O2", "title": "Payouts net margin reaches 85% range",                                           "target": 85,      "unit": "%",           "current_value": 0},
    {"id": "KR6",  "objective_id": "O2", "title": "JPM integration live and processing volume by Q2 close",                         "target": 1,       "unit": "binary",      "current_value": 0},
    # O3 — AI Experience
    {"id": "KR7",  "objective_id": "O3", "title": "AI-resolved tickets reach 250 per month",                                        "target": 250,     "unit": "tickets/month","current_value": 0},
    {"id": "KR8",  "objective_id": "O3", "title": "Automated CX resolution rate reaches 55%",                                       "target": 55,      "unit": "%",           "current_value": 0},
    {"id": "KR9",  "objective_id": "O3", "title": "Aura CSAT score reaches at least 80%",                                           "target": 80,      "unit": "%",           "current_value": 0},
    # O4 — AI Monetization
    {"id": "KR10", "objective_id": "O4", "title": "AI Lead Scraper MQL-to-SQL conversion rate reaches 50%",                         "target": 50,      "unit": "%",           "current_value": 0},
    {"id": "KR11", "objective_id": "O4", "title": "AI Money Manager reaches $10K MRR by Dec 2026",                                  "target": 10000,   "unit": "$/month",     "current_value": 0},
    # O5 — AI Monetization
    {"id": "KR12", "objective_id": "O5", "title": "Core operational workflows migrated to AI Agentic Workflow framework and live in production", "target": 5, "unit": "workflows", "current_value": 0},
    # O6 — Security & Compliance Ops
    {"id": "KR13", "objective_id": "O6", "title": "ISO 27001 pre-audit completed with PASS result",                                 "target": 1,       "unit": "binary",      "current_value": 0},
]

OBJ_HEADERS = ["id", "title", "sub_team", "quarter", "company_vision"]
KR_HEADERS  = ["id", "objective_id", "title", "target", "unit", "current_value"]
UPD_HEADERS    = ["id", "kr_id", "new_value", "week_notes", "blockers", "confidence", "updated_by", "updated_at"]
NOTES_HEADERS  = ["id", "sub_team", "quarter", "week_number", "content", "updated_by", "updated_at"]
CHARTS_HEADERS = ["id", "sub_team", "quarter", "week_number", "filename", "drive_file_id", "drive_url", "uploaded_by", "uploaded_at"]


def _ensure_worksheet(spreadsheet, title, headers):
    try:
        ws = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(headers))
        ws.append_row(headers, value_input_option="RAW")
    return ws


@st.cache_data(ttl=3600)
def _needs_migration() -> bool:
    """Return True if the objectives sheet uses the old schema (no sub_team column)."""
    try:
        ws = get_spreadsheet().worksheet("objectives")
        headers = ws.row_values(1)
        return "sub_team" not in headers
    except gspread.WorksheetNotFound:
        return False


def _wipe_worksheets(spreadsheet) -> None:
    for name in ["objectives", "key_results", "kr_updates"]:
        try:
            ws = spreadsheet.worksheet(name)
            spreadsheet.del_worksheet(ws)
        except gspread.WorksheetNotFound:
            pass


def seed_if_empty() -> None:
    if st.session_state.get("seed_checked"):
        return

    spreadsheet = get_spreadsheet()

    if _needs_migration():
        _needs_migration.clear()
        _wipe_worksheets(spreadsheet)

    obj_ws = _ensure_worksheet(spreadsheet, "objectives",  OBJ_HEADERS)
    kr_ws  = _ensure_worksheet(spreadsheet, "key_results", KR_HEADERS)
    _ensure_worksheet(spreadsheet, "kr_updates",    UPD_HEADERS)
    _ensure_worksheet(spreadsheet, "weekly_notes",  NOTES_HEADERS)
    _ensure_worksheet(spreadsheet, "weekly_charts", CHARTS_HEADERS)

    if not obj_ws.get_all_records():
        obj_ws.append_rows(
            [[o["id"], o["title"], o["sub_team"], o["quarter"], o["company_vision"]]
             for o in SEED_OBJECTIVES],
            value_input_option="RAW",
        )

    if not kr_ws.get_all_records():
        kr_ws.append_rows(
            [[kr["id"], kr["objective_id"], kr["title"], kr["target"], kr["unit"], kr["current_value"]]
             for kr in SEED_KEY_RESULTS],
            value_input_option="RAW",
        )

    st.session_state["seed_checked"] = True


# ---------------------------------------------------------------------------
# Read helpers (cached 30 s)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def load_objectives() -> pd.DataFrame:
    ws = get_spreadsheet().worksheet("objectives")
    records = ws.get_all_records()
    return pd.DataFrame(records) if records else pd.DataFrame(columns=OBJ_HEADERS)


@st.cache_data(ttl=60)
def load_key_results() -> pd.DataFrame:
    ws = get_spreadsheet().worksheet("key_results")
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=KR_HEADERS)
    df = pd.DataFrame(records)
    for col in ["target", "current_value"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


@st.cache_data(ttl=60)
def load_updates() -> pd.DataFrame:
    ws = get_spreadsheet().worksheet("kr_updates")
    records = ws.get_all_records()
    return pd.DataFrame(records) if records else pd.DataFrame(columns=UPD_HEADERS)


def load_updates_for_kr(kr_id: str) -> pd.DataFrame:
    df = load_updates()
    if df.empty:
        return df
    filtered = df[df["kr_id"] == kr_id].copy()
    return filtered.sort_values("updated_at", ascending=False) if not filtered.empty else filtered


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def update_kr_value(
    kr_id: str,
    new_value: float,
    week_notes: str,
    blockers: str,
    confidence: int,
    updated_by: str,
) -> None:
    """Atomically append update log row and update current_value in key_results."""
    spreadsheet = get_spreadsheet()
    kr_ws  = spreadsheet.worksheet("key_results")
    upd_ws = spreadsheet.worksheet("kr_updates")

    all_krs = kr_ws.get_all_records()
    row_index = None
    for i, row in enumerate(all_krs, start=2):
        if str(row.get("id", "")) == str(kr_id):
            row_index = i
            break

    if row_index is None:
        raise ValueError(f"KR '{kr_id}' not found in sheet.")

    headers = kr_ws.row_values(1)
    col_index = headers.index("current_value") + 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    update_id = str(uuid.uuid4())[:8]

    upd_ws.append_row(
        [update_id, kr_id, new_value, week_notes, blockers, confidence, updated_by, now],
        value_input_option="RAW",
    )
    kr_ws.update_cell(row_index, col_index, new_value)

    st.cache_data.clear()


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

def compute_progress(row: Any) -> float:
    target  = float(row.get("target", 0) or 0)
    current = float(row.get("current_value", 0) or 0)
    if target == 0:
        return 100.0 if current > 0 else 0.0
    return max(0.0, min(100.0, current / target * 100))


# ---------------------------------------------------------------------------
# Delete / Edit
# ---------------------------------------------------------------------------

def delete_update_by_id(update_id: str) -> None:
    """Delete a kr_update row by ID and recalculate the parent KR's current_value."""
    spreadsheet = get_spreadsheet()
    upd_ws = spreadsheet.worksheet("kr_updates")

    all_updates = upd_ws.get_all_records()

    kr_id = None
    for row in all_updates:
        if str(row.get("id", "")) == str(update_id):
            kr_id = str(row.get("kr_id", ""))
            break

    if kr_id is None:
        raise ValueError(f"Update '{update_id}' not found.")

    cell = upd_ws.find(str(update_id), in_column=1)
    if cell:
        upd_ws.delete_rows(cell.row)

    remaining = sorted(
        [r for r in all_updates
         if str(r.get("kr_id", "")) == kr_id and str(r.get("id", "")) != str(update_id)],
        key=lambda r: str(r.get("updated_at", "")),
        reverse=True,
    )
    new_value = float(remaining[0].get("new_value", 0) or 0) if remaining else 0.0

    kr_ws = spreadsheet.worksheet("key_results")
    all_krs = kr_ws.get_all_records()
    headers = kr_ws.row_values(1)
    for i, row in enumerate(all_krs, start=2):
        if str(row.get("id", "")) == kr_id:
            col_index = headers.index("current_value") + 1
            kr_ws.update_cell(i, col_index, new_value)
            break

    st.cache_data.clear()


def delete_kr_by_id(kr_id: str) -> None:
    """Delete a KR row and all its associated updates."""
    spreadsheet = get_spreadsheet()
    kr_ws  = spreadsheet.worksheet("key_results")
    upd_ws = spreadsheet.worksheet("kr_updates")

    cell = kr_ws.find(str(kr_id), in_column=1)
    if cell:
        kr_ws.delete_rows(cell.row)

    all_updates = upd_ws.get_all_records()
    rows_to_delete = [
        i for i, row in enumerate(all_updates, start=2)
        if str(row.get("kr_id", "")) == str(kr_id)
    ]
    for row_num in reversed(rows_to_delete):
        upd_ws.delete_rows(row_num)

    st.cache_data.clear()


def update_kr_fields(kr_id: str, title: str, target: float, unit: str) -> None:
    """Update a KR's title, target, and unit in Google Sheets."""
    spreadsheet = get_spreadsheet()
    kr_ws = spreadsheet.worksheet("key_results")
    all_krs = kr_ws.get_all_records()
    headers = kr_ws.row_values(1)

    for i, row in enumerate(all_krs, start=2):
        if str(row.get("id", "")) == str(kr_id):
            if "title" in headers:
                kr_ws.update_cell(i, headers.index("title") + 1, title)
            if "target" in headers:
                kr_ws.update_cell(i, headers.index("target") + 1, target)
            if "unit" in headers:
                kr_ws.update_cell(i, headers.index("unit") + 1, unit)
            break

    st.cache_data.clear()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def _next_obj_id() -> str:
    records = get_spreadsheet().worksheet("objectives").get_all_records()
    nums = [int(str(r.get("id", ""))[1:])
            for r in records
            if str(r.get("id", "")).startswith("O") and str(r.get("id", ""))[1:].isdigit()]
    return f"O{max(nums, default=0) + 1}"


def _next_kr_id() -> str:
    records = get_spreadsheet().worksheet("key_results").get_all_records()
    nums = [int(str(r.get("id", ""))[2:])
            for r in records
            if str(r.get("id", "")).startswith("KR") and str(r.get("id", ""))[2:].isdigit()]
    return f"KR{max(nums, default=0) + 1}"


def create_objective(title: str, sub_team: str, quarter: str) -> None:
    """Append a new objective row and clear the read cache."""
    ws = get_spreadsheet().worksheet("objectives")
    new_id = _next_obj_id()
    ws.append_row([new_id, title, sub_team, quarter, ""], value_input_option="RAW")
    st.cache_data.clear()


def create_kr(objective_id: str, title: str, target: float, unit: str) -> None:
    """Append a new key result row and clear the read cache."""
    ws = get_spreadsheet().worksheet("key_results")
    new_id = _next_kr_id()
    ws.append_row([new_id, objective_id, title, target, unit, 0], value_input_option="RAW")
    st.cache_data.clear()


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Weekly Notes
# ---------------------------------------------------------------------------

def get_week_number() -> int:
    """Return current ISO week number."""
    return datetime.now().isocalendar()[1]


@st.cache_data(ttl=60)
def get_weekly_note(sub_team: str, quarter: str, week_number: int) -> dict:
    ws = get_worksheet("weekly_notes")
    rows = ws.get_all_records()
    for row in rows:
        if (row["sub_team"] == sub_team and
                row["quarter"] == quarter and
                str(row["week_number"]) == str(week_number)):
            return row
    return {}


def save_weekly_note(sub_team: str, quarter: str, week_number: int, content: str, updated_by: str) -> None:
    ws = get_worksheet("weekly_notes")
    rows = ws.get_all_records()
    for i, row in enumerate(rows, start=2):
        if (row["sub_team"] == sub_team and
                row["quarter"] == quarter and
                str(row["week_number"]) == str(week_number)):
            ws.update(f"E{i}:G{i}", [[content, updated_by, datetime.now(timezone.utc).isoformat()]])
            st.cache_data.clear()
            return
    all_rows = ws.get_all_values()
    existing_ids = [int(r[0]) for r in all_rows[1:] if str(r[0]).isdigit()]
    next_id = max(existing_ids) + 1 if existing_ids else 1
    ws.append_row(
        [next_id, sub_team, quarter, week_number, content, updated_by,
         datetime.now(timezone.utc).isoformat()],
        value_input_option="RAW",
    )
    st.cache_data.clear()


# ---------------------------------------------------------------------------
# Weekly Charts (Google Drive)
# ---------------------------------------------------------------------------

def get_or_create_drive_folder(drive_service: Any, path: str) -> str:
    """Create folder hierarchy in Drive and return the leaf folder ID."""
    parts = path.split("/")
    parent_id = "root"
    for part in parts:
        query = (
            f"name='{part}' and '{parent_id}' in parents "
            f"and mimeType='application/vnd.google-apps.folder' "
            f"and trashed=false"
        )
        results = drive_service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])
        if files:
            parent_id = files[0]["id"]
        else:
            folder = drive_service.files().create(
                body={"name": part, "parents": [parent_id],
                      "mimeType": "application/vnd.google-apps.folder"},
                fields="id",
            ).execute()
            parent_id = folder["id"]
    return parent_id


def upload_charts_to_drive(files: list, sub_team: str, quarter: str, week_number: int, uploaded_by: str) -> None:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    import io as _io

    creds = get_service_account_credentials()
    drive_service = build("drive", "v3", credentials=creds)
    folder_id = get_or_create_drive_folder(
        drive_service, f"OKR Dashboard/{quarter}/{sub_team}/Week {week_number}"
    )

    charts_ws = get_worksheet("weekly_charts")
    all_rows = charts_ws.get_all_values()
    existing_ids = [int(r[0]) for r in all_rows[1:] if str(r[0]).isdigit()]
    next_id = max(existing_ids) + 1 if existing_ids else 1

    for file in files:
        file.seek(0)
        media = MediaIoBaseUpload(_io.BytesIO(file.read()), mimetype=file.type, resumable=True)
        try:
            drive_file = drive_service.files().create(
                body={"name": file.name, "parents": [folder_id]},
                media_body=media,
                fields="id, webViewLink",
            ).execute()
        except Exception as e:
            st.error(f"Error creating file '{file.name}' in Drive: {e}")
            if hasattr(e, "content"):
                st.write(f"Error details: {e.content.decode()}")
            raise e

        try:
            drive_service.permissions().create(
                fileId=drive_file["id"],
                body={"type": "anyone", "role": "reader"},
            ).execute()
        except Exception as e:
            st.warning(f"Could not set public permissions for '{file.name}': {e}")
            # Non-fatal, we can still use the file if the service account has access

        direct_url = f"https://drive.google.com/uc?export=view&id={drive_file['id']}"
        charts_ws.append_row(
            [next_id, sub_team, quarter, week_number, file.name,
             drive_file["id"], direct_url, uploaded_by,
             datetime.now(timezone.utc).isoformat()],
            value_input_option="RAW",
        )
        next_id += 1

    st.cache_data.clear()


@st.cache_data(ttl=60)
def get_weekly_charts(sub_team: str, quarter: str, week_number: int) -> list:
    ws = get_worksheet("weekly_charts")
    rows = ws.get_all_records()
    return [r for r in rows if (
        r["sub_team"] == sub_team and
        r["quarter"] == quarter and
        str(r["week_number"]) == str(week_number)
    )]


def delete_chart_from_drive(chart_id: str) -> None:
    from googleapiclient.discovery import build
    creds = get_service_account_credentials()
    drive_service = build("drive", "v3", credentials=creds)

    ws = get_worksheet("weekly_charts")
    rows = ws.get_all_records()
    for i, row in enumerate(rows, start=2):
        if str(row["id"]) == str(chart_id):
            drive_service.files().delete(fileId=str(row["drive_file_id"])).execute()
            ws.delete_rows(i)
            st.cache_data.clear()
            return


# ---------------------------------------------------------------------------
# PDF import helpers
# ---------------------------------------------------------------------------

def find_or_create_objective(title: str, sub_team: str, quarter: str) -> str:
    ws = get_worksheet("objectives")
    rows = ws.get_all_records()
    for row in rows:
        if (str(row["title"]).strip() == title.strip() and
                row["sub_team"] == sub_team and
                row["quarter"] == quarter):
            return str(row["id"])
    create_objective(title, sub_team, quarter)
    rows = ws.get_all_records()
    return str(rows[-1]["id"])


def find_or_create_kr(objective_id: str, title: str, target: float, unit: str) -> str:
    ws = get_worksheet("key_results")
    rows = ws.get_all_records()
    for row in rows:
        if (str(row["objective_id"]) == str(objective_id) and
                str(row["title"]).strip() == title.strip()):
            return str(row["id"])
    create_kr(objective_id, title, float(target or 0), unit)
    rows = ws.get_all_records()
    return str(rows[-1]["id"])


def save_parsed_pdf_data(parsed_data: dict, sub_team: str, quarter: str, updated_by: str) -> None:
    for obj_data in parsed_data.get("objectives", []):
        obj_id = find_or_create_objective(obj_data["title"], sub_team, quarter)
        for kr_data in obj_data.get("key_results", []):
            kr_id = find_or_create_kr(
                obj_id,
                kr_data["title"],
                kr_data.get("target") or 0,
                kr_data.get("unit", ""),
            )
            if kr_data.get("current_value") is not None:
                update_kr_value(
                    kr_id=kr_id,
                    new_value=float(kr_data["current_value"]),
                    week_notes=f"Imported from PDF — Status: {kr_data.get('status', 'N/A')}",
                    blockers="",
                    confidence=3,
                    updated_by=updated_by,
                )

    if parsed_data.get("weekly_updates"):
        week_number = get_week_number()
        combined_notes = "\n\n".join([
            f"**{u['section']}**\n{u['content']}"
            for u in parsed_data["weekly_updates"]
        ])
        save_weekly_note(sub_team, quarter, week_number, combined_notes, updated_by)


# ---------------------------------------------------------------------------
def format_value(current: float, target: float, unit: str) -> str:
    u = unit.lower().strip()
    if u == "binary":
        return "✓ Done" if current >= 1 else "Pending"
    if u == "$" or u == "$/month":
        sym = "$"
        def fmt(v):
            if v >= 1_000_000:
                return f"{sym}{v/1_000_000:.1f}M"
            if v >= 1_000:
                return f"{sym}{v/1_000:.0f}K"
            return f"{sym}{v:,.0f}"
        return f"{fmt(current)} / {fmt(target)}"
    if u == "%":
        return f"{current:.1f}% / {target:.0f}%"
    return f"{current:g} / {target:g} {unit}"
