# Quick Start: Testing the HTML Export Fix

## What Was Fixed?
Per-KR narratives (week_notes, confidence, blockers) now display below each KR instead of just showing one team-level comment.

## 30-Second Test

1. **Generate fresh HTML:**
   - Open Streamlit app
   - Click **"Report"** button
   - Download the HTML file

2. **Open in browser:**
   - Right-click HTML file → Open with Browser
   - OR drag-and-drop into browser

3. **Verify the fix:**
   - Look for a KR with updates
   - Scroll down slightly below that KR row
   - You should see a shaded box with:
     - "Update: [some text from week_notes]"
     - "Confidence: [value]" (if filled in)
     - "Blockers: [text]" (if filled in)

**Result:** ✅ If you see individual KR narratives, the fix is working!

## What You're Looking For

### Good ✅ (After the fix)
```
┌─ KEY RESULT: Deploy 5x per week
│  Status: ON TRACK | Progress: 100% | Target: 5 number
├─ Update: Successfully deployed to production
│  Confidence: High
│
├─ KEY RESULT: Reduce build time
│  Status: AT RISK | Progress: 40% | Target: 2h
├─ Update: Found bottleneck in npm install step
│  Confidence: Medium
│  Blockers: Need npm cache optimization
│
├─ KEY RESULT: Monitor uptime
│  Status: BLOCKED | Progress: 0% | Target: 1 number
├─ No updates recorded
```

### Bad ❌ (Before the fix)
```
┌─ KEY RESULT: Deploy 5x per week
│  Status: ON TRACK | Progress: 100% | Target: 5 number
│
├─ KEY RESULT: Reduce build time
│  Status: AT RISK | Progress: 40% | Target: 2h
│
├─ KEY RESULT: Monitor uptime
│  Status: BLOCKED | Progress: 0% | Target: 1 number
│
└─ [Repeated team comment on ALL KRs ← BAD]
```

## Detailed 5-Minute Test

### Step 1: Generate HTML
```
Streamlit App → Header → Click [Report] button → Download HTML
```

### Step 2: Open in Browser
```
Open the downloaded HTML file in your browser
```

### Step 3: Check Metrics
Scroll to find a team section. You should see 4 metric cards:
- **Objectives:** [number]
- **Key Results:** [number]
- **On Track:** [number]
- **At Risk:** [number]

For each metric:
- Count the KRs with ≥75% progress → should match "On Track"
- Count the KRs with <50% progress → should match "At Risk"

✅ **If counts match:** Metrics are working correctly

### Step 4: Check Per-KR Narratives
For each KR in the table:
1. Look at the KR title and status
2. Look IMMEDIATELY BELOW (in the same table)
3. You should see a shaded narrative block with:
   - "Update: [week_notes]" (if there's an update)
   - "Confidence: [value]" (if confidence is set)
   - "Blockers: [text]" (if blockers are set)
   - OR "No updates recorded" (if nothing above)

✅ **If you see individual narratives for each KR:** Fix is working!

### Step 5: Check Team Comment Still Works
Scroll to the BOTTOM of each team section.
You should see "Context & Updates" with a team-level comment.

This is SEPARATE from the per-KR narratives above.

✅ **If you see the team-level comment at the end:** Everything is working!

## Common Questions

### Q: I don't see any narratives. What's wrong?
**A:** Narratives only show if KRs have updates. Check:
1. Are there any rows in the `kr_updates` sheet?
2. Is the `week_notes` column filled in for any KRs?
3. If no updates exist, you'll see "No updates recorded" for all KRs ✅ (This is correct)

### Q: The metrics are wrong. What do I check?
**A:** Manually count:
1. How many KRs show ≥75% progress?
2. How many KRs show <50% progress?
3. Do these counts match the metric cards?

If yes → Metrics are correct ✅
If no → There might be a data filtering issue (see `METRICS_CALCULATION_GUIDE.md`)

### Q: Why are different KRs showing different narratives now?
**A:** **This is the fix!** Before, all KRs in a team would show the same team-level comment. Now each KR shows its own narrative from the latest update.

### Q: Where are the team-level comments?
**A:** They're still there, but now at the BOTTOM of each team section, not repeated on each KR.

## Visual Checklist

Use this as you review the HTML:

```
┌─ Team Metrics
│  ├─ [number] Objectives ← Count of objectives
│  ├─ [number] Key Results ← Count of KRs
│  ├─ [number] On Track ← KRs ≥75%
│  └─ [number] At Risk ← KRs <50%
│
├─ Objectives
│  └─ Objective 1: [title]
│     ├─ KR 1: [title]
│     │  ├─ Status badge, Progress %, Target
│     │  └─ Narrative: Week notes + Confidence + Blockers ← NEW!
│     │
│     ├─ KR 2: [title]
│     │  ├─ Status badge, Progress %, Target
│     │  └─ Narrative: Different from KR 1 ← NEW!
│     │
│     └─ KR 3: [title]
│        ├─ Status badge, Progress %, Target
│        └─ Narrative: Different again ← NEW!
│
├─ [More objectives...]
│
└─ Context & Updates ← Team-level comment (appears once at end)
   └─ "This week we focused on..."
```

## Files That Can Help

- `CHANGES_SUMMARY.md` — What changed and why
- `HTML_EXPORT_TEST_CHECKLIST.md` — Full testing guide
- `METRICS_CALCULATION_GUIDE.md` — How metrics work
- `HTML_EXPORT_BEFORE_AFTER.md` — Visual before/after

## Still Have Issues?

1. **Review the generated HTML's source code:**
   - Right-click → Inspect Element
   - Look for `class="kr-narrative"`
   - Check if week_notes content is there

2. **Check the data:**
   - Open the Google Sheet
   - Go to `kr_updates` sheet
   - Verify `week_notes` column has content
   - Verify `updated_at` has recent dates

3. **Check the filtering:**
   - Are you looking at the right quarter?
   - Are you looking at the right team?
   - Are the KRs you expect actually there?

## Success Criteria ✅

The fix is working if:
- [ ] You see individual narratives below each KR
- [ ] Different KRs show different narratives (not all the same)
- [ ] Narratives contain week_notes, confidence, and/or blockers
- [ ] At least one KR shows "No updates recorded" (if you have one without updates)
- [ ] Team-level "Context & Updates" appears at the end
- [ ] Metrics (On Track / At Risk) match manual count

---

**Ready to test?** Follow the 30-second test above, then report back! 🚀
