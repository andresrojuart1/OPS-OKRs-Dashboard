# HTML Export: Before & After the Fix

## Before Fix ❌

```
┌─ Team: Operations ─────────────────────────────────────┐
│ Objectives: 3    Key Results: 8                        │
│ On Track: 2      At Risk: 4                            │
│                                                        │
│ OBJECTIVE: Improve CI/CD Pipeline                      │
│ ┌─────────────────────────────────────────────────────┐│
│ │ KEY RESULT              │ STATUS      │ PROGRESS     ││
│ ├─────────────────────────┼─────────────┼──────────────┤│
│ │ Deploy 5x per week      │ ON TRACK    │ 100%         ││
│ │ Reduce build time       │ AT RISK     │ 40%          ││
│ │ 99.9% uptime            │ BLOCKED     │ 0%           ││
│ └─────────────────────────────────────────────────────┘│
│                                                        │
│ [At the very end of the team section:]               │
│ Context & Updates                                      │
│ "This week we focused on the deployment pipeline.    │
│  Started work on build optimization. Found issues    │
│  with the Docker layer."                             │
│                                                        │
│ ⚠️ PROBLEM: This ONE team-level comment appears      │
│    for ALL KRs in that team. Users can't tell which  │
│    KR the comment is about!                          │
└─────────────────────────────────────────────────────────┘
```

## After Fix ✅

```
┌─ Team: Operations ─────────────────────────────────────┐
│ Objectives: 3    Key Results: 8                        │
│ On Track: 2      At Risk: 4                            │
│                                                        │
│ OBJECTIVE: Improve CI/CD Pipeline                      │
│ ┌─────────────────────────────────────────────────────┐│
│ │ KEY RESULT              │ STATUS      │ PROGRESS     ││
│ ├─────────────────────────┼─────────────┼──────────────┤│
│ │ Deploy 5x per week      │ ON TRACK    │ 100%         ││
│ ├─────────────────────────┴─────────────┴──────────────┤│ ← NEW
│ │ Update: 5 deployments completed this week            ││ ← NEW
│ │ Confidence: High                                      ││ ← NEW
│ └────────────────────────────────────────────────────────┘│ ← NEW
│                                                        │
│ │ Reduce build time       │ AT RISK     │ 40%          ││
│ ├─────────────────────────┴─────────────┴──────────────┤│ ← NEW
│ │ Update: Identified bottleneck in npm install step    ││ ← NEW
│ │ Confidence: Medium                                    ││ ← NEW
│ │ Blockers: Waiting on npm cache layer optimization    ││ ← NEW
│ └────────────────────────────────────────────────────────┘│ ← NEW
│                                                        │
│ │ 99.9% uptime            │ BLOCKED     │ 0%           ││
│ ├─────────────────────────┴─────────────┴──────────────┤│ ← NEW
│ │ No updates recorded                                   ││ ← NEW
│ └────────────────────────────────────────────────────────┘│ ← NEW
│ └─────────────────────────────────────────────────────┘│
│                                                        │
│ [At the very end of the team section:]               │
│ Context & Updates                                      │
│ "This week we focused on the deployment pipeline.    │
│  Started work on build optimization. Found issues    │
│  with the Docker layer."                             │
│                                                        │
│ ✅ SOLUTION: Each KR now has its own narrative       │
│    directly beneath it, showing updates specific to   │
│    that KR. Team-level note still at the end.        │
└─────────────────────────────────────────────────────────┘
```

## The Key Change

### Data Structure

**Before:**
```
KR Row 1: "Deploy 5x per week" → 100% ON TRACK
KR Row 2: "Reduce build time" → 40% AT RISK        (same team comment?)
KR Row 3: "99.9% uptime" → 0% BLOCKED              (still the same comment?)
[Team-level comment shown once at the end]
```

**After:**
```
KR Row 1: "Deploy 5x per week" → 100% ON TRACK
└─ Narrative Block: "Update: 5 deployments completed..."
    └─ Confidence: High

KR Row 2: "Reduce build time" → 40% AT RISK
└─ Narrative Block: "Update: Identified bottleneck..."
    └─ Confidence: Medium
    └─ Blockers: Waiting on npm cache...

KR Row 3: "99.9% uptime" → 0% BLOCKED
└─ Narrative Block: "No updates recorded"

[Team-level comment shown at the end]
```

## What Data Gets Extracted

For each KR, the HTML export now looks at the **latest update** and extracts:

| Field | Source | Display | Example |
|-------|--------|---------|---------|
| `new_value` | kr_updates | Progress % | "100%" |
| `week_notes` | kr_updates | Update narrative | "5 deployments completed this week" |
| `confidence` | kr_updates | Confidence level | "High", "Medium", "Low" |
| `blockers` | kr_updates | Dependencies/blockers | "Waiting on npm cache layer optimization" |

All fields are **per-KR** from the latest update in that week/period.

## Visual Hierarchy

```
┌─ Metric Cards (At Team Level)
│  ├─ 3 Objectives
│  ├─ 8 Key Results
│  ├─ 2 On Track      ← Calculated from all KR progress
│  └─ 4 At Risk       ← Calculated from all KR progress
│
├─ Objective Block
│  └─ KR Table
│     ├─ KR Row 1
│     │  ├─ Title, Status Badge, Progress %, Target
│     │  └─ Narrative Block ← NEW!
│     │     ├─ Update (from week_notes)
│     │     ├─ Confidence (if provided)
│     │     └─ Blockers (if provided)
│     ├─ KR Row 2
│     │  └─ Narrative Block ← NEW!
│     └─ KR Row 3
│        └─ Narrative Block ← NEW!
│
└─ Team-Level Context & Updates
   └─ "This week we..." (from weekly_notes sheet)
```

## The Fix in One Sentence

> **Extract individual KR update details (week_notes, confidence, blockers) and display them below each KR in the HTML table, so users can see what's happening with each KR instead of just seeing a team-level comment.**
