# HTML Export Fixes — Per-KR Narratives & Metrics Display

## Problem Statement
The HTML export was not displaying individual KR-level narratives, causing:
1. The same team-level comment appearing on all KRs (incorrect)
2. Loss of per-KR update context (week_notes, blockers, confidence)
3. User unable to see which updates each KR had from the generated report

## Root Cause Analysis
**In html_export.py (lines 550-594):**
- The KR table generation loop extracted `new_value` from updates_df
- It calculated and displayed the correct **metrics** (on_track, at_risk counts)
- **BUT** it did not extract or display the narrative fields: `week_notes`, `blockers`, `confidence`
- Only team-level narrative from `weekly_notes` sheet was appended (line 606)

## Solution Implemented

### 1. Extract Per-KR Narrative Fields (lines 550-565)
```python
# For each KR, get the latest update and extract:
kr_narrative = str(latest.get("week_notes", "")).strip()
kr_blockers = str(latest.get("blockers", "")).strip()
kr_confidence = str(latest.get("confidence", "")).strip()
```

### 2. Add CSS Styling for KR Narratives (lines 341-357)
```css
.kr-narrative {
    background: rgba(122, 80, 247, 0.08);
    border-left: 3px solid #7A50F7;
    padding: 12px;
    margin-top: 8px;
}

.kr-narrative-empty {
    color: #6B7280;
    font-style: italic;
}
```

### 3. Display Per-KR Narrative Below Each KR Row (lines 595-620)
After each KR row in the table, a new row is added that displays:
- **Update:** The week_notes from the latest update (HTML-escaped, newlines converted to <br>)
- **Confidence:** The confidence value (if present)
- **Blockers:** The blockers/dependencies (if present)
- **Empty state:** "No updates recorded" if no narrative data exists

**HTML Structure:**
```html
<tr style="background: rgba(122, 80, 247, 0.03);">
    <td colspan="4">
        <div class="kr-narrative">
            <strong>Update:</strong> [week_notes]
            <strong>Confidence:</strong> [confidence]
            <strong>Blockers:</strong> [blockers]
        </div>
    </td>
</tr>
```

## Affected Columns in Updates DataFrame
The fix uses these fields from the `kr_updates` worksheet:
- `kr_id` — Links to KR (already used)
- `new_value` — Progress value (already used)
- `week_notes` — **NEW** → Narrative update for the KR
- `blockers` — **NEW** → Blockers/dependencies for the KR
- `confidence` — **NEW** → Confidence level for the KR
- `updated_at` — Latest timestamp (already used for sorting)

## Metrics Calculation (Unchanged)
The on_track and at_risk calculations remain correct:
```python
# Lines 478-493: Calculate metrics for each team
for _, kr in team_krs.iterrows():
    kr_id = str(kr["id"])
    kr_updates = updates_df[updates_df["kr_id"] == kr_id]
    # ... get current value ...
    pct = (current / target * 100) if target > 0 else 0
    
    if pct >= 75:
        on_track += 1
    elif pct < 50:
        at_risk += 1
```

**Metric Categories:**
- **On Track:** 75% ≤ progress (always positive)
- **In Progress:** 50% ≤ progress < 75% (not counted in metrics)
- **At Risk:** progress < 50% (includes 0% = BLOCKED)

## Testing the Fix

### 1. Verify Per-KR Narratives Display
- Open the HTML export in a browser
- For each KR, there should be a narrative block below the row
- The narrative should show:
  - The specific update (week_notes) for that KR
  - Confidence level (if provided)
  - Any blockers/dependencies (if provided)

### 2. Verify Metrics Are Correct
- Count the KRs with ≥75% progress → should match "On Track" count
- Count the KRs with <50% progress → should match "At Risk" count
- Example: If 3 KRs are BLOCKED (0%) and none are ON TRACK, metrics show 0 On Track, 3 At Risk

### 3. Verify Team-Level Narrative Still Shows
- Scroll to the bottom of each team's section
- The "Context & Updates" section should still display the team-level note from weekly_notes
- This is separate from the per-KR narratives

## Files Modified
- **html_export.py**
  - Lines 341-357: Added `.kr-narrative` and `.kr-narrative-empty` CSS classes
  - Lines 550-565: Extract per-KR narrative fields (week_notes, blockers, confidence)
  - Lines 595-620: Display per-KR narrative blocks below each KR row

## Data Flow
```
Google Sheets (kr_updates)
    ↓
load_updates() → updates_df
    ↓
generate_html_report(updates_df, ...)
    ├─ Lines 478-493: Calculate metrics using updates_df
    │   ├─ for each KR: get latest update → extract new_value → calc progress %
    │   ├─ pct >= 75 → on_track++
    │   └─ pct < 50 → at_risk++
    │
    └─ Lines 550-620: Generate KR table rows
        ├─ for each KR: get latest update
        ├─ extract: new_value (progress), week_notes, blockers, confidence
        ├─ display: KR title, status, progress bar
        └─ display: narrative block with week_notes, confidence, blockers
```

## Why This Works
1. **Correct granularity:** Each KR gets its own narrative from its latest update
2. **Clean separation:** Per-KR narratives (from kr_updates) vs team-level narratives (from weekly_notes)
3. **Rich context:** Users see progress % + status + specific update notes all together
4. **Graceful degradation:** If a KR has no updates, it shows "No updates recorded" instead of breaking

## Performance Impact
- **Minimal:** The extraction happens in the same loop that was already iterating KRs
- **No new queries:** Uses the updates_df already passed to the function
- **No HTML size bloat:** Narrative blocks are collapsed by default (browser rendering)
