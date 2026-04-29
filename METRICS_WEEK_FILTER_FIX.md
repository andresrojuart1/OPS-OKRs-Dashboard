# Metrics Week Filter Fix ✅

## Problem
The HTML report was showing metrics from **all weeks**, not just the selected week (W16).

**Example:**
- Dashboard (W16): 14 On Track, 3 At Risk
- HTML Report: Different numbers (showing data from previous weeks too)

## Root Cause
In `html_export.py`, when calculating metrics (lines 478-493), the code was getting the **latest update from ANY week**:

```python
kr_updates = updates_df[updates_df["kr_id"] == kr_id]
latest = kr_updates.sort_values("updated_at", ascending=False).iloc[0]  # Latest from any week!
```

The `updates_df` passed to the function contained updates from all weeks, so it was pulling old data.

## Solution Applied

### 1. Modified Function Signature (Line 95)
**Before:**
```python
def generate_html_report(
    objectives_df, krs_df, updates_df, notes_df,
    quarter="Q2 2026", charts_df=None,
):
```

**After:**
```python
def generate_html_report(
    objectives_df, krs_df, updates_df, notes_df,
    quarter="Q2 2026", charts_df=None,
    selected_week=None,  # ← NEW PARAMETER
):
```

### 2. Filter Updates by Week (Lines 114-119)
Added at the beginning of the function:
```python
# Filter updates by selected week if provided
if selected_week is not None and not updates_df.empty:
    if "week_number" in updates_df.columns:
        updates_df = updates_df[
            pd.to_numeric(updates_df["week_number"], errors="coerce") == selected_week
        ].copy()
```

### 3. Updated Function Call in app.py (Line 839)
**Before:**
```python
html_content = generate_html_report(
    objectives_df=objectives_df,
    krs_df=krs_df,
    updates_df=updates_df,
    notes_df=notes_df,
    quarter=selected_quarter,
    charts_df=charts_df,
)
```

**After:**
```python
html_content = generate_html_report(
    objectives_df=objectives_df,
    krs_df=krs_df,
    updates_df=updates_df,
    notes_df=notes_df,
    quarter=selected_quarter,
    charts_df=charts_df,
    selected_week=selected_week,  # ← ADDED
)
```

## How It Works Now

**Flow:**
```
User selects Week 16 in dashboard
     ↓
Clicks "Report" button
     ↓
selected_week = 16 is passed to generate_html_report()
     ↓
updates_df is filtered to only include week_number == 16
     ↓
Metrics are calculated from week 16 updates only
     ↓
HTML shows correct metrics that match dashboard
```

## Result

Now when you:
1. Select **Week 16** in the dashboard
2. Click **Report**
3. Download and open the HTML

**The metrics will match exactly what you see in the dashboard! ✅**

## Testing

To verify the fix:
1. Look at dashboard metrics for Week 16 (e.g., 14 On Track, 3 At Risk)
2. Generate HTML report
3. Open HTML and check team metrics
4. Numbers should match perfectly

## Files Modified
- `app.py` — Line 839: Pass `selected_week` parameter
- `html_export.py` — Lines 95, 114-119: Add parameter and filtering logic
