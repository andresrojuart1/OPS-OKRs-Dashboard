# Ontop OPS OKRs Dashboard — Q2 2026

Streamlit app with Google OAuth (restricted to `@getontop.com`) and Google Sheets as the live backend.

---

## Quick start

```bash
# 1. Clone / open the project
cd "OPS OKRs Dashboard"

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure credentials
cp .env.example .env
# → Fill in all values in .env (see sections below)

# 5. Run
streamlit run app.py
```

---

## Credential setup

### A. Google OAuth 2.0 (user login)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create an **OAuth 2.0 Client ID** (Web application)
3. Add Authorized redirect URIs:
   - `http://localhost:8501/oauth2callback` (local dev)
   - `https://your-app.streamlit.app/oauth2callback` (production)
4. Copy **Client ID** → `GOOGLE_CLIENT_ID`
5. Copy **Client Secret** → `GOOGLE_CLIENT_SECRET`

### B. Google Sheets (data backend)

1. Create a new Google Sheet — copy its ID from the URL → `GSPREAD_SPREADSHEET_ID`
   - URL pattern: `https://docs.google.com/spreadsheets/d/<ID>/edit`
2. Go to APIs & Services → Credentials → Create **Service Account**
3. Grant it no project roles (not needed)
4. Create a JSON key for the service account → download the file
5. Run `python -c "import json; print(json.dumps(json.load(open('key.json'))))"` to get a single-line JSON string → paste as `GOOGLE_SERVICE_ACCOUNT_JSON`
6. **Share the Google Sheet** with the service account email (found in the JSON as `client_email`) with **Editor** access

### C. `.env` file

```env
GOOGLE_CLIENT_ID=...apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8501/oauth2callback
GSPREAD_SPREADSHEET_ID=...
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

---

## Deploy to Streamlit Community Cloud

1. Push repo to GitHub (make sure `.env` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select repo + `app.py`
3. Under **Advanced settings → Secrets**, paste the `.env` contents in TOML format:
   ```toml
   GOOGLE_CLIENT_ID = "..."
   GOOGLE_CLIENT_SECRET = "..."
   GOOGLE_REDIRECT_URI = "https://your-app.streamlit.app/oauth2callback"
   GSPREAD_SPREADSHEET_ID = "..."
   GOOGLE_SERVICE_ACCOUNT_JSON = '{"type":"service_account",...}'
   ```
4. Update the OAuth redirect URI in Google Cloud Console to match the Streamlit Cloud URL

---

## Architecture

```
app.py              → Page config, CSS, router (login vs dashboard)
auth.py             → Google OAuth flow, domain restriction, logout
sheets.py           → gspread client (service account), seed, CRUD, cache
components/
  sidebar.py        → User profile, objective nav, sign-out
  objective_card.py → Card + KR rows with progress bars
  kr_update_modal.py→ Inline update form (writes to Sheets + audit log)
.streamlit/
  config.toml       → Dark theme (#0D0E1A background, purple primary)
```

### Google Sheets schema

| Sheet | Columns |
|-------|---------|
| `objectives` | id, title, owner, quarter |
| `key_results` | id, objective_id, title, unit, target, baseline, current_value, direction |
| `kr_updates` | timestamp, kr_id, old_value, new_value, updated_by, note |

The app seeds these sheets automatically on first run if they are empty.

---

## Multi-user collaboration

- All writes go through `sheets.py:update_kr_value()` which is atomic (append log row + update cell)
- Read cache TTL is 30 seconds (`@st.cache_data(ttl=30)`)
- Each user sees a refresh of everyone else's changes within 30 s
