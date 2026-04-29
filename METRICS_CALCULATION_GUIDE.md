# KR Metrics Calculation — How On Track & At Risk Are Counted

## Overview

The HTML report displays 4 metrics at the team level:
1. **Objectives** — Count of unique objectives
2. **Key Results** — Count of KRs in those objectives
3. **On Track** — Count of KRs with ≥75% progress
4. **At Risk** — Count of KRs with <50% progress

## Status Categories

Every KR falls into exactly one category based on its **progress percentage**:

```
Progress Percentage → Status → Counted In Which Metric
─────────────────────────────────────────────────────
      ≥ 75%        → ON TRACK      → "On Track" metric
   50% - 74%       → IN PROGRESS   → (not counted in metrics)
    1% - 49%       → AT RISK       → "At Risk" metric
      0%           → BLOCKED       → "At Risk" metric
```

## Calculation Logic

**File:** `html_export.py`, Lines 478-493

```python
# For each KR in a team:
for _, kr in team_krs.iterrows():
    kr_id = str(kr["id"])
    
    # Get the latest update (most recent by updated_at)
    kr_updates = updates_df[updates_df["kr_id"] == kr_id]
    if not kr_updates.empty:
        latest = kr_updates.sort_values("updated_at", ascending=False).iloc[0]
        current = float(latest.get("new_value", 0))
    else:
        # Fallback to static current_value if no updates
        current = float(kr.get("current_value", 0))
    
    target = float(kr.get("target", 0))
    
    # Calculate percentage
    pct = (current / target * 100) if target > 0 else 0
    
    # Count in appropriate bucket
    if pct >= 75:
        on_track += 1      # ✅ Good progress
    elif pct < 50:
        at_risk += 1       # ⚠️  Falling behind
    # (else: 50-74% not counted in metrics, shown as "IN PROGRESS")
```

## Data Sources

The calculation uses:

| Field | Source | Purpose |
|-------|--------|---------|
| `new_value` | kr_updates sheet | Current progress value |
| `current_value` | key_results sheet | Fallback if no recent update |
| `target` | key_results sheet | Goal value for the KR |
| `updated_at` | kr_updates sheet | To find "latest" update |

## Example Scenario

**Team: Operations**

| KR Title | Target | Current (latest update) | Progress % | Status | Metric |
|----------|--------|------------------------|------------|--------|---------|
| Deploy 5x per week | 5 | 5 | 100% | ON TRACK | ✅ |
| Reduce build time | 2h | 0.9h | 45% | AT RISK | ⚠️ |
| 99.9% uptime | 1 | 0 | 0% | BLOCKED | ⚠️ |
| Add monitoring | 10 tasks | 8 tasks | 80% | ON TRACK | ✅ |
| Security audit | 1 | 0.5 | 50% | IN PROGRESS | — |

**Result:**
- **Objectives:** 1 (all 5 KRs belong to same objective)
- **Key Results:** 5
- **On Track:** 2 (Deploy + Monitoring)
- **At Risk:** 2 (Build time + Uptime)
- **(In Progress):** 1 (Security, not counted)

## Key Points

### 1. Latest Update Always Used
If a KR has multiple updates in the `kr_updates` sheet, we always use the **most recent** one (sorted by `updated_at` descending, take first).

### 2. Both Progress & Status Matter
The percentage determines **both**:
- Which status badge is shown (ON TRACK / IN PROGRESS / AT RISK / BLOCKED)
- Whether it's counted in the "On Track" or "At Risk" metrics

### 3. Zero Progress = At Risk
KRs with 0% progress show as **BLOCKED** (status badge) and are counted as **At Risk** (metric).

This is semantically correct: a blocked KR is at risk of not meeting its goal.

### 4. Metrics Ignore In-Progress KRs
KRs between 50-75% progress:
- Show as "IN PROGRESS" badge
- Are NOT counted in either metric
- This keeps metrics focused on the extremes (good vs. bad)

## Why This Calculation Works

**Three-bucket approach (On Track, In Progress, At Risk) + two metrics (On Track, At Risk) creates clear visibility:**

```
Healthy     → On Track ✅       (≥75%)   [Counted: Yes]
Okay        → In Progress       (50-74%) [Counted: No]
Concerning  → At Risk ⚠️        (<50%)   [Counted: Yes]
```

Leadership sees at a glance:
- "How many are doing well?" → On Track count
- "How many need attention?" → At Risk count
- "How many are neither?" → Total KRs - On Track - At Risk

## Testing the Metrics

To verify metrics are calculating correctly:

1. **List all KRs in the report**
2. **For each KR, check:**
   - What's the target? (column: "Target")
   - What's the current value? (progress % shown)
   - What status badge is shown?
3. **Count:**
   - How many show ≥75% progress?
   - How many show <50% progress?
4. **Compare to metrics displayed:**
   - "On Track" metric should equal your count of ≥75%
   - "At Risk" metric should equal your count of <50%

## Example Check

If the HTML shows:
```
AI Monetization: On Track = 0, At Risk = 3
```

Then all 3 KRs in that section should have <50% progress:
- ✅ Correct if you see: 0%, 0%, 25% (all <50%)
- ❌ Wrong if you see: 100%, 0%, 0% (one is ≥75%)

## Debugging Metrics Issues

**If metrics don't match what you see in KRs:**

1. **Check the data source:**
   - Is the `kr_updates` sheet being populated?
   - Are the `new_value` and `updated_at` fields filled in?

2. **Check the filtering:**
   - Are objectives and KRs filtered by team/quarter?
   - Are updates filtered to only active KRs?

3. **Check the calculation:**
   - Look at line 486-493 in html_export.py
   - Verify that `target > 0` (avoid division by zero)
   - Verify that `new_value` is numeric (not text)

4. **Check the sorting:**
   - Is the latest update actually the most recent?
   - Check `updated_at` timestamp in the data

## Performance Note

The metrics calculation is O(n) where n = number of KRs in team:
- For each KR: look up latest update (pandas filter)
- Calculate percentage
- Increment counter

For typical team sizes (5-20 KRs), this is negligible.

## Future Enhancements

Possible improvements to the metrics system:

1. **Weighted metrics:** "Confidence-weighted on track" = on_track_count × avg_confidence
2. **Trend metrics:** "KRs improving" = count of KRs with week-over-week progress increase
3. **SLA metrics:** "KRs on pace" = count of KRs that will hit target if current pace continues
4. **Risk breakdown:** Show "At Risk" subcategories (e.g., "Blocked: 2, Behind Schedule: 3")
