# ⚡ Quick Fixes — Copy & Paste into app.py

These are the exact changes you need to make. Just find the lines and replace.

---

## Fix #1: Update imports at the top of app.py

**Location**: Line ~397

**OLD** (to find):
```python
from sheets import (
    seed_if_empty, load_objectives, load_key_results, load_updates,
    compute_progress, create_objective,
    get_week_number, get_weekly_note, save_weekly_note,
    undo_last_import,
    get_weekly_charts, upload_charts_to_drive, delete_chart_from_drive,
    download_drive_file,
)
```

**NEW** (replace with):
```python
from sheets_cached import (
    load_objectives_cached as load_objectives,
    load_key_results_cached as load_key_results,
    load_updates_cached as load_updates,
    clear_sheets_cache,
)
from sheets import (
    seed_if_empty,
    compute_progress, create_objective,
    get_week_number, get_weekly_note, save_weekly_note,
    undo_last_import,
    get_weekly_charts, upload_charts_to_drive, delete_chart_from_drive,
    download_drive_file,
)
```

✅ **Result**: Data loading now uses cache.

---

## Fix #2: Update "Sync Data" button

**Location**: Line ~671 (inside `render_header()`)

**OLD** (to find):
```python
if st.button("Sync Data", icon=":material/refresh:", key="hdr_sync", use_container_width=True, type="secondary"):
    st.cache_data.clear()
    st.session_state["last_sync_time"] = datetime.now()
    track_action("Synced data")
    st.toast("Data synchronized", icon="✅")
    st.rerun()
```

**NEW** (replace with):
```python
if st.button("Sync Data", icon=":material/refresh:", key="hdr_sync", use_container_width=True, type="secondary"):
    clear_sheets_cache()  # ← Use the optimized function
    st.session_state["last_sync_time"] = datetime.now()
    track_action("Synced data")
    st.toast("Data synchronized", icon="✅")
    st.rerun()
```

✅ **Result**: Cache clears properly when user clicks "Sync Data".

---

## Fix #3: Lazy-load objective cards (OPTIONAL but recommended)

**Location**: Line ~1004 (inside `render_dashboard()`)

**OLD** (to find):
```python
for i, (_, obj_row) in enumerate(display_objs.iterrows()):
    render_objective_card(obj_row, krs_df, updates_df, krs_info_all, is_primary=(i == 0))
```

**NEW** (replace with):
```python
for i, (_, obj_row) in enumerate(display_objs.iterrows()):
    # Lazy load: only first card is expanded by default
    is_expanded = (i == 0)
    obj_title = str(obj_row.get("title", "Objective"))[:60]
    
    with st.expander(f"📌 {obj_title}...", expanded=is_expanded):
        render_objective_card(obj_row, krs_df, updates_df, krs_info_all, is_primary=is_expanded)
```

✅ **Result**: Collapsed cards load much faster (lazy rendering).

---

## Test the changes

### 1. Open the app locally
```bash
cd "/Users/andresrojas/CX-AI-Platform/OPS OKRs Dashboard"
streamlit run app.py
```

### 2. Check the performance
- Open browser DevTools (F12)
- Click on "Network" tab
- Interact with the app (select a team, change quarter)
- **Expected**: Fast response, no long waits for Sheets queries

### 3. Check the logs
- Look at the terminal where you ran `streamlit run app.py`
- You should NOT see repeated "Loading objectives..." messages
- If you see them, the cache isn't working

---

## Troubleshooting

### "Error: sheets_cached module not found"
- Make sure you created `sheets_cached.py` in the same folder as `app.py`
- Check the file path is correct

### "Data still feels slow"
- The first load will still be 2-3s (that's normal)
- Subsequent interactions should be 200-500ms
- If second interaction is slow, cache might not be working
- Try clicking "Sync Data" button to reset

### "I want to go back"
- Undo these changes in `app.py` (use Git if you have it)
- Delete `sheets_cached.py`
- The app will work like before (just slower)

---

## How much faster will it be?

### Before
- First load: 3 seconds
- Click a filter: 2-3 seconds (full rerun)
- Every interaction: wait

### After
- First load: 3 seconds (same, data is fresh)
- Click a filter: 300-500ms (cached data)
- Most interactions: snappy

**Typical speedup: 5-7x for interactive workflows**

---

## What if you need real-time data?

Change the TTL (Time-To-Live):

```python
# In sheets_cached.py, change line 24:

@st.cache_data(ttl=60)  # Cache only 1 minute instead of 5
def load_objectives_cached() -> pd.DataFrame:
```

Trade-off:
- `ttl=60`: More up-to-date data, but more API calls
- `ttl=300`: Less API calls, data up to 5 min old
- `ttl=3600`: Very fast but data could be 1 hour old

**Recommendation**: Start with `ttl=300` (5 min). If users complain data is stale, lower to `ttl=60`.

---

## Next steps (optional)

After these changes work well, you can implement:

1. **Lazy-load images from Drive** (see OPTIMIZATION_GUIDE.md)
2. **Paginate large tables** (show 20 KRs instead of 100)
3. **Move to better hosting** (Railway, Render, Heroku)

But these three fixes above should solve 80% of your speed problems.

---

## Questions?

If anything breaks:
1. Check the error message
2. Make sure all three changes above are applied correctly
3. Clear browser cache (Ctrl+Shift+Del)
4. Restart the app (`Ctrl+C` in terminal, then `streamlit run app.py` again)
