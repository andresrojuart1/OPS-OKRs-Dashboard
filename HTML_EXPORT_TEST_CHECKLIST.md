# HTML Export Test Checklist

Use this checklist to verify that the HTML export is working correctly after the fixes.

## Pre-Test Setup

- [ ] Make sure at least one KR has an update with `week_notes` filled in
- [ ] Make sure at least one KR has a `confidence` value in its latest update
- [ ] Make sure at least one KR has `blockers` filled in
- [ ] Make sure at least one KR has NO updates (to test "No updates recorded" state)

## Test 1: Generate Fresh HTML Report

**Goal:** Verify that the HTML export is picking up the latest data

Steps:
1. [ ] Open the Streamlit app
2. [ ] Click the **"Report"** button to generate HTML
3. [ ] Open the downloaded HTML file in a browser
4. [ ] Verify it renders without errors

Expected Result:
- [ ] HTML loads with proper styling
- [ ] All team sections visible
- [ ] Metric cards show numbers (Objectives, KRs, On Track, At Risk)

## Test 2: Verify Metric Calculations

**Goal:** Ensure on_track and at_risk counts are correct

Steps:
1. [ ] Open the HTML report in browser
2. [ ] For each team section:
   - [ ] Find the metric cards at the top
   - [ ] Count how many KRs have ≥75% progress (should match "On Track")
   - [ ] Count how many KRs have <50% progress (should match "At Risk")
   - [ ] Verify the count matches

Example:
```
Team: Operations
Metric Cards Show: On Track = 2, At Risk = 3
KR Progress Percentages: 100%, 80%, 45%, 20%, 0%
Check: ≥75% = 2 KRs ✅, <50% = 3 KRs ✅
```

## Test 3: Verify Per-KR Narratives Display

**Goal:** Verify that each KR shows its own narrative, not repeated team comments

Steps:
1. [ ] Find a KR with a `week_notes` update
2. [ ] Look directly below that KR's row
3. [ ] Verify you see:
   - [ ] A shaded narrative block
   - [ ] The word "Update:" followed by the week_notes content
   - [ ] The week_notes content is specific to that KR

Example (correct):
```
┌─ KR: Deploy 5x per week
│  Status: ON TRACK | Progress: 100%
├─ Update: Successfully deployed 5 times this week
│  Confidence: High
└─ [Next KR section]

┌─ KR: Reduce build time
│  Status: AT RISK | Progress: 40%
├─ Update: Found bottleneck in npm install, plan to optimize
│  Confidence: Medium
│  Blockers: Waiting on npm cache layer
└─ [Next KR section]
```

## Test 4: Verify Confidence & Blockers Display

**Goal:** Verify that confidence and blockers are shown when present

Steps:
1. [ ] Find a KR with confidence value set
2. [ ] Verify the narrative block shows:
   - [ ] "Confidence: [value]"
3. [ ] Find a KR with blockers set
4. [ ] Verify the narrative block shows:
   - [ ] "Blockers: [text]"

## Test 5: Test "No Updates Recorded" State

**Goal:** Verify that KRs without updates show the fallback message

Steps:
1. [ ] Find a KR that has NO updates in the updates sheet
2. [ ] Look at its narrative block
3. [ ] Verify you see:
   - [ ] Light text "No updates recorded" (in italics, gray color)

## Test 6: HTML Quality & Styling

**Goal:** Verify that the narrative blocks look good and don't break the layout

Steps:
1. [ ] Check narrative block styling:
   - [ ] Background color is subtle (light purple tint)
   - [ ] Text is readable
   - [ ] Indentation/padding looks good
2. [ ] Check narrative block placement:
   - [ ] Each narrative block appears directly below its KR row
   - [ ] Multiple narratives don't overlap
   - [ ] Table structure still intact
3. [ ] Check on mobile (if applicable):
   - [ ] [ ] Narratives display properly on narrow screens
   - [ ] [ ] Text doesn't overflow

## Test 7: Verify Team-Level Comment Still Works

**Goal:** Ensure team-level "Context & Updates" still appears at the end

Steps:
1. [ ] Scroll to the bottom of each team's section
2. [ ] Verify you see:
   - [ ] A section titled "Context & Updates"
   - [ ] The team-level notes from the `weekly_notes` sheet
3. [ ] Verify this is DIFFERENT from the per-KR narratives above

Example structure:
```
[Multiple KRs with per-KR narratives above]
...
[At the bottom of team section:]
┌─ Context & Updates
│  "This week the team focused on... [team-level comment]"
└─
```

## Test 8: Verify No Data Loss

**Goal:** Ensure existing KR data (title, status, progress %) is unchanged

Steps:
1. [ ] Spot-check 3-5 KRs in the HTML:
   - [ ] Title matches what's in the Streamlit app
   - [ ] Progress % matches the dashboard
   - [ ] Status badge matches (ON TRACK / AT RISK / etc.)
   - [ ] Target value is correct

## Test 9: Multi-Team Scenario

**Goal:** Verify the fix works when there are multiple teams

Steps:
1. [ ] If dashboard has multiple teams:
   - [ ] [ ] Generate HTML with all teams
   - [ ] [ ] Verify each team has its own metric cards
   - [ ] [ ] Verify each team's KRs have individual narratives
   - [ ] [ ] Verify team-level "Context & Updates" only appears once per team

## Test 10: Print/PDF Export

**Goal:** Verify the HTML prints well (for future PDF workflow)

Steps:
1. [ ] Open HTML in browser
2. [ ] Try Ctrl+P (or Cmd+P) to print preview
3. [ ] Check:
   - [ ] Narrative blocks don't break across pages
   - [ ] Colors/styling visible in print (if color mode selected)
   - [ ] No text cutoff on right side

## Edge Cases

Test these edge cases to ensure robustness:

### Edge Case 1: KR with very long narrative
- [ ] Add a week_notes with 500+ characters
- [ ] Verify it wraps properly without breaking layout
- [ ] Newlines convert to line breaks (<br> tags)

### Edge Case 2: KR with no target (division by zero)
- [ ] Set target to 0 for a KR
- [ ] Verify it shows "0%" not error
- [ ] Verify it counts as BLOCKED

### Edge Case 3: KR with text blockers (special characters)
- [ ] Add blockers with quotes, <, >, &, etc.
- [ ] Verify they're HTML-escaped (safe display)

### Edge Case 4: Empty updates_df (no updates at all)
- [ ] Temporarily comment out updates loading
- [ ] Verify all KRs show "No updates recorded"
- [ ] Verify metrics still calculate (using current_value from key_results)

## Regression Tests

Ensure nothing broke:

- [ ] KRs still display with correct title
- [ ] Status badges still show correct color
- [ ] Progress bars still render with correct width
- [ ] Target values display correctly
- [ ] Tables are still sortable (if implemented)
- [ ] Hover effects on table rows still work
- [ ] Page layout is responsive (mobile-friendly)
- [ ] Dark theme still applies
- [ ] All colors match design system

## Sign-Off

- [ ] All tests passed
- [ ] No unexpected behavior observed
- [ ] Per-KR narratives are displayed correctly
- [ ] Metrics calculations are correct
- [ ] HTML is production-ready

**Tester:** ________________
**Date:** ________________
**Notes:** ____________________________________________________

## Known Limitations (Expected Behavior)

1. **Week-level filtering:** The HTML export shows ALL updates for each KR, not just the selected week. If you need week-specific reporting, a new version would be needed.

2. **Multiple updates per KR:** Only the LATEST update is shown. If you need all updates shown, that would require a different layout.

3. **Confidence/Blockers optional:** These fields are optional. If not filled in, they simply don't display.

4. **Team-level note vs KR notes:** Only one team-level note is shown (the latest one). Per-KR notes come from the latest update for each KR. These are intentionally separate.
