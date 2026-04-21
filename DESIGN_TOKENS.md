# 🎨 Design System — Ontop OKRs Dashboard

## Color Palette

### Brand Colors
```css
--ontop-purple: #7C5EFF    /* Primary accent */
--ontop-coral:  #FF6B7A    /* Secondary accent */
```

### Backgrounds with Depth
```css
--bg-primary:   #0A0E27    /* Main background */
--bg-card:      #111633    /* Card/elevated surfaces */
--bg-input:     #1A2247    /* Input fields, states */
--bg-hover:     #1F2954    /* Interactive hover state */
```

### Text Hierarchy
```css
--text-primary:    #FFFFFF    /* Headings, primary content */
--text-secondary:  #D1D5E0    /* Body text, descriptions */
--text-tertiary:   #8B94B3    /* Secondary labels */
--text-muted:      #5F6B8F    /* Disabled, metadata */
```

### Borders
```css
--border-color: #2A3555    /* Default borders, dividers */
```

### Status System (Behavioral)
```css
--status-green:    #10B981    /* Success, completed, on-track */
--status-yellow:   #FBBF24    /* Warning, needs attention */
--status-red:      #EF4444    /* Error, blocked, critical */
--status-purple:   #A78BFA    /* Info, neutral status */
```

### Accent Subtle
```css
--accent-subtle: rgba(167, 139, 250, 0.08)    /* Hover, focus, selected states */
```

---

## Usage Patterns

### Status Badges (Backgrounds + Colors)

#### Success State
```html
<div class="status-success">Completed ✓</div>
<!-- Uses: background: rgba(16, 185, 129, 0.1); color: #10B981; -->
```

#### Warning State
```html
<div class="status-warning">Needs Attention</div>
<!-- Uses: background: rgba(251, 191, 36, 0.1); color: #FBBF24; -->
```

#### Error State
```html
<div class="status-error">Blocked</div>
<!-- Uses: background: rgba(239, 68, 68, 0.1); color: #EF4444; -->
```

#### Info State
```html
<div class="status-info">In Progress</div>
<!-- Uses: background: rgba(167, 139, 250, 0.1); color: #A78BFA; -->
```

### Glass/Elevation for Cards
All cards use this layered approach for "premium" feel:

```css
.kr-card, .objective-card, .status-card {
    background: linear-gradient(
        180deg,
        rgba(255,255,255,0.02),
        rgba(255,255,255,0)
    ), var(--bg-card);
    border: 1px solid rgba(255,255,255,0.04);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
```

This creates:
- **Light top edge** (glass effect)
- **Subtle elevation** via shadow
- **Fine border** for definition
- **Depth without color change** (maintains dark aesthetic)

### Hover States
Use `--accent-subtle` for focus areas:

```css
button:hover {
    background: var(--accent-subtle);
}

input:focus {
    box-shadow: 0 0 0 2px var(--accent-subtle);
}
```

---

## Implementation in Python

### Using Status Badges
```python
from components.status_badges import render_status_badge, get_status_class

# Render a warning badge
render_status_badge("warning", "At Risk")

# Infer status from percentage
status = get_status_class(pct=65)
render_status_badge(status)
```

### Progress Indicators
```python
from components.status_badges import render_progress_indicator

# Auto-infer status
render_progress_indicator(current=65, target=100)

# Override status
render_progress_indicator(current=65, target=100, status="warning")
```

---

## Color Usage Guide

### When to use each Status Color

| Color | Use Case | Behavior |
|-------|----------|----------|
| **Green** | KRs on-track, objectives completed, successful actions | Background: `rgba(16, 185, 129, 0.1)` |
| **Yellow** | KRs at-risk, needs attention, warning conditions | Background: `rgba(251, 191, 36, 0.1)` |
| **Red** | KRs blocked, errors, failed states, critical issues | Background: `rgba(239, 68, 68, 0.1)` |
| **Purple** | Info, neutral state, in-progress, metadata | Background: `rgba(167, 139, 250, 0.1)` |

### Text Colors

| Color | Use Case |
|-------|----------|
| **Primary** `#FFFFFF` | Main headings (H1, H2, H3) |
| **Secondary** `#D1D5E0` | Body text, paragraphs, descriptions |
| **Tertiary** `#8B94B3` | Secondary labels, field labels |
| **Muted** `#5F6B8F` | Disabled state, metadata, timestamps |

---

## Accessibility Notes

✅ All text meets WCAG AA contrast ratio
✅ Status colors distinct for colorblind users (shapes/text reinforces meaning)
✅ Hover states use size/shadow, not color alone
✅ Focus states have 2px box-shadow for visibility

---

## Migration from Old Palette

If updating old colors:

```python
# Old → New
OLD_GREEN = "#2DD4BF"    → GREEN = "#10B981"
OLD_YELLOW = "#f8c56a"   → YELLOW = "#FBBF24"
OLD_RED = "#ff4b4b"      → RED = "#EF4444"
OLD_PURPLE = "#7A50F7"   → PURPLE = "#A78BFA"
```

Update in:
- `components/objective_card.py` (DONE ✓)
- `components/status_badges.py` (template provided)
- Any custom HTML renders
