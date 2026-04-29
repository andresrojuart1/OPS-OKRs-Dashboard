# Status Color Fix - Show Correct Visual Status ✅

## The Problem User Found

**HTML Report showing:**
- 25% progress → AT RISK (🟠 orange/yellow)
- 45% progress → AT RISK (🟠 orange/yellow)

**Dashboard showing:**
- 25% progress → ON TRACK (🟢 green)
- 45% progress → ON TRACK (🟢 green)

Why? They were using different thresholds to determine the color!

## Root Cause

The HTML had TWO separate places where status was determined:

### 1. Metrics Counting (FIXED in previous update)
```python
# This was comparing against expected_pct (dynamic) ✅
if pct >= expected_pct:
    on_track += 1
```

### 2. Status Badge Color (WAS BROKEN)
```python
# This was comparing against hardcoded 75% (static) ❌
if pct >= 75:
    status = "ON TRACK"  # green
elif pct >= 50:
    status = "IN PROGRESS"  # cyan
elif pct > 0:
    status = "AT RISK"  # orange
else:
    status = "BLOCKED"  # red
```

**The Inconsistency:**
- 25% >= 23.08% (expected_pct) → counts as "On Track" for metrics ✅
- 25% < 75% (hardcoded) → shows as "AT RISK" badge ❌

## The Fix

Changed lines 640-651 in html_export.py to use the dynamic threshold:

### Before (Broken)
```python
# Determine status
if pct >= 75:           # ❌ Hardcoded
    status = "ON TRACK"
    status_class = "status-on-track"
elif pct >= 50:         # ❌ Hardcoded
    status = "IN PROGRESS"
    status_class = "status-in-progress"
elif pct > 0:
    status = "AT RISK"
    status_class = "status-at-risk"
else:
    status = "BLOCKED"
    status_class = "status-blocked"
```

### After (Fixed)
```python
# Determine status using dynamic threshold (same as dashboard)
if pct >= expected_pct:  # ✅ Dynamic
    status = "ON TRACK"
    status_class = "status-on-track"
elif pct > 0:
    status = "AT RISK"
    status_class = "status-at-risk"
else:
    status = "BLOCKED"
    status_class = "status-blocked"
```

## How It Works Now

### Week 16 Example

```
expected_pct = 23.08% (because 3 weeks elapsed of 13 total)

KR 1: 25% progress
  - Meets expected_pct (25 >= 23.08) → ON TRACK 🟢
  - Color: Green
  - Status badge: "ON TRACK"

KR 2: 45% progress
  - Meets expected_pct (45 >= 23.08) → ON TRACK 🟢
  - Color: Green
  - Status badge: "ON TRACK"

KR 3: 10% progress
  - Below expected_pct (10 < 23.08) → AT RISK 🟠
  - Color: Orange
  - Status badge: "AT RISK"

KR 4: 0% progress
  - Blocked → BLOCKED 🔴
  - Color: Red
  - Status badge: "BLOCKED"
```

## Status Badge Logic Now

**Unified Across Dashboard and HTML:**

```
Progress < expected_pct AND > 0%  →  AT RISK 🟠 (orange)
Progress >= expected_pct          →  ON TRACK 🟢 (green)
Progress = 0%                     →  BLOCKED 🔴 (red)
```

No more "IN PROGRESS" status because the dynamic threshold already captures progress status.

## Why This Matters

The colors now tell the **correct story for the week you're in:**

- **Early in quarter** (week 14): expected_pct = 7.7%
  - 10% progress = 🟢 On Track (ahead of schedule)
  - 5% progress = 🟠 At Risk (behind schedule)

- **Mid quarter** (week 20): expected_pct = 53.8%
  - 50% progress = 🟠 At Risk (falling behind)
  - 60% progress = 🟢 On Track (on schedule)

- **End of quarter** (week 26): expected_pct = 100%
  - 90% progress = 🟠 At Risk (won't finish)
  - 100% progress = 🟢 On Track (completed)

The expected threshold **scales with time**, so colors are relative to the actual week.

## Files Modified

- `html_export.py` — Lines 640-651 (status determination logic)

## Testing

1. **Open dashboard**, select **Week 16**
2. **Look at KRs with 25-45% progress** → Should show 🟢 green status
3. **Click Report**
4. **Open HTML**
5. **Find same KRs** → Should ALSO show 🟢 green status
6. **Verify colors match perfectly** ✅

## Before vs After

### HTML Report - Before Fix ❌
```
KR: "CS Intelligence System..."
Progress: 25%
Status: AT RISK 🟠 (wrong color)
```

### HTML Report - After Fix ✅
```
KR: "CS Intelligence System..."
Progress: 25%
Status: ON TRACK 🟢 (correct color)
```

### Dashboard (Always Correct) ✅
```
KR: "CS Intelligence System..."
Progress: 25%
Status: ON TRACK 🟢 (matches HTML now!)
```

## Consistency Check

Both Dashboard and HTML now use this logic:

**Metrics Counting:**
```python
if pct >= expected_pct:
    on_track += 1
```

**Status Badge Color:**
```python
if pct >= expected_pct:
    status = "ON TRACK"  # green
```

**Both use expected_pct** ✅ → **Visual colors match metrics** ✅

## Summary

- Dashboard was using dynamic threshold (correct)
- HTML was using hardcoded 75% for colors (wrong)
- Now HTML uses same dynamic threshold for colors
- Colors now match the dashboard perfectly for every week
