"""
Diagnostic script to check Sheets connection and data.

Run this to debug data loading issues:
    python diagnose.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

print("=" * 60)
print("OPS OKRs Dashboard — Diagnostic Check")
print("=" * 60)

# Check 1: Environment variables
print("\n✓ Checking environment variables...")
required_vars = [
    "GSPREAD_SPREADSHEET_ID",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "GOOGLE_SERVICE_ACCOUNT_FILE",
]

for var in required_vars:
    val = os.getenv(var, "")
    status = "✅" if val else "❌"
    if var == "GOOGLE_SERVICE_ACCOUNT_JSON":
        display = f"(present, {len(val)} chars)" if val else "(missing)"
    else:
        display = f"'{val}'" if val else "(empty)"
    print(f"  {status} {var}: {display}")

# Check 2: Can we import Sheets module?
print("\n✓ Checking imports...")
try:
    from sheets import get_gspread_client, get_worksheet
    print("  ✅ sheets module imported successfully")
except Exception as e:
    print(f"  ❌ Failed to import sheets: {e}")
    sys.exit(1)

# Check 3: Can we connect to Google Sheets?
print("\n✓ Connecting to Google Sheets...")
try:
    client = get_gspread_client()
    print("  ✅ Connected to Google API")
except Exception as e:
    print(f"  ❌ Failed to connect: {e}")
    sys.exit(1)

# Check 4: Can we access the spreadsheet?
print("\n✓ Accessing spreadsheet...")
try:
    from sheets import get_spreadsheet
    sheet = get_spreadsheet()
    print(f"  ✅ Opened spreadsheet: '{sheet.title}'")
except Exception as e:
    print(f"  ❌ Failed to open spreadsheet: {e}")
    sys.exit(1)

# Check 5: Can we read each worksheet?
print("\n✓ Checking worksheets...")
worksheets_to_check = ["objectives", "key_results", "updates"]

for ws_name in worksheets_to_check:
    try:
        ws = get_worksheet(ws_name)
        if not ws:
            print(f"  ❌ '{ws_name}': Not found")
            continue

        records = ws.get_all_records()
        row_count = len(records)

        if row_count == 0:
            print(f"  ⚠️  '{ws_name}': Found but empty (0 rows)")
        else:
            col_count = len(records[0]) if records else 0
            print(f"  ✅ '{ws_name}': {row_count} rows × {col_count} cols")

            # Show first row
            if records:
                first_row = records[0]
                print(f"       Columns: {', '.join(first_row.keys())}")
    except Exception as e:
        print(f"  ❌ '{ws_name}': Error — {e}")

# Check 6: Test caching module
print("\n✓ Testing caching module...")
try:
    from sheets_cached import (
        load_objectives_cached,
        load_key_results_cached,
        load_updates_cached,
    )
    print("  ✅ sheets_cached module imported successfully")

    # Try to load data
    print("\n✓ Loading cached data (first call, will fetch from Sheets)...")
    objs = load_objectives_cached()
    krs = load_key_results_cached()
    updates = load_updates_cached()

    print(f"  ✅ Objectives: {len(objs)} rows")
    print(f"  ✅ Key Results: {len(krs)} rows")
    print(f"  ✅ Updates: {len(updates)} rows")

    if not objs.empty:
        print(f"     Objectives columns: {list(objs.columns)}")
    if not krs.empty:
        print(f"     KRs columns: {list(krs.columns)}")
    if not updates.empty:
        print(f"     Updates columns: {list(updates.columns)}")

except Exception as e:
    import traceback
    print(f"  ❌ Failed to load cached data: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Diagnostic complete!")
print("=" * 60)
