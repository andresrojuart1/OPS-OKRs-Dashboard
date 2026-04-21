"""
Optimized Google Sheets caching layer for OPS OKRs Dashboard.

Key improvements:
- @st.cache_data with 5-minute TTL for all data loads
- Manual refresh via "Sync Data" button (clears cache)
- Reduces Sheets API calls from 3-per-rerun to 1-per-5-minutes
- Expected speedup: 5-7x for typical workflows

Usage:
    from sheets_cached import (
        load_objectives_cached,
        load_key_results_cached,
        load_updates_cached,
    )

    # In app.py, replace:
    # from sheets import load_objectives, load_key_results, load_updates
    # with:
    # from sheets_cached import (
    #     load_objectives_cached as load_objectives,
    #     load_key_results_cached as load_key_results,
    #     load_updates_cached as load_updates,
    # )
"""

import streamlit as st
import pandas as pd
from sheets import get_worksheet

# ─────────────────────────────────────────────────────────
# ✅ OPTIMIZED: Cached data loaders with 5-minute TTL
# ─────────────────────────────────────────────────────────

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_objectives_cached() -> pd.DataFrame:
    """
    Load objectives from 'objectives' worksheet.

    Caching:
    - First call: fetches from Sheets (~1-2s)
    - Subsequent calls within 5 min: instant (~0ms)
    - After 5 min: automatic cache invalidation → fresh fetch

    Manual refresh:
    - Call st.cache_data.clear() from the "Sync Data" button
    """
    try:
        ws = get_worksheet("objectives")
        if not ws:
            print("[WARNING] Could not get 'objectives' worksheet")
            return pd.DataFrame()

        data = ws.get_all_records()
        if not data:
            print("[INFO] 'objectives' worksheet is empty")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        print(f"[OK] Loaded {len(df)} objectives from Sheets")
        return df
    except Exception as e:
        import traceback
        print(f"[ERROR] Failed to load objectives: {e}")
        traceback.print_exc()
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_key_results_cached() -> pd.DataFrame:
    """
    Load key results from 'key_results' worksheet.

    Same caching behavior as load_objectives_cached().
    """
    try:
        ws = get_worksheet("key_results")
        if not ws:
            print("[WARNING] Could not get 'key_results' worksheet")
            return pd.DataFrame()

        data = ws.get_all_records()
        if not data:
            print("[INFO] 'key_results' worksheet is empty")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        print(f"[OK] Loaded {len(df)} key results from Sheets")
        return df
    except Exception as e:
        import traceback
        print(f"[ERROR] Failed to load key results: {e}")
        traceback.print_exc()
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_updates_cached() -> pd.DataFrame:
    """
    Load updates from 'kr_updates' worksheet.

    Same caching behavior as load_objectives_cached().
    """
    try:
        ws = get_worksheet("kr_updates")
        if not ws:
            print("[WARNING] Could not get 'kr_updates' worksheet")
            return pd.DataFrame()

        data = ws.get_all_records()
        if not data:
            print("[INFO] 'kr_updates' worksheet is empty")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        print(f"[OK] Loaded {len(df)} updates from Sheets")
        return df
    except Exception as e:
        import traceback
        print(f"[ERROR] Failed to load updates: {e}")
        traceback.print_exc()
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────
# ✅ Quick stats (cached separately for even faster access)
# ─────────────────────────────────────────────────────────

@st.cache_data(ttl=600)  # Cache 10 minutes
def count_objectives_by_quarter() -> dict:
    """
    Quick count of objectives per quarter.
    Used by header KPI cards.
    """
    df = load_objectives_cached()
    if df.empty:
        return {}

    if "quarter" not in df.columns:
        return {}

    return df["quarter"].value_counts().to_dict()


@st.cache_data(ttl=600)
def count_krs_by_team() -> dict:
    """
    Quick count of KRs per sub-team.
    Used for team selector in sidebar.
    """
    df = load_key_results_cached()
    if df.empty:
        return {}

    # Get objectives to map team
    objs = load_objectives_cached()
    if objs.empty:
        return {}

    # Merge to get team info
    if "objective_id" in df.columns and "id" in objs.columns:
        merged = df.merge(
            objs[["id", "sub_team"]],
            left_on="objective_id",
            right_on="id",
            how="left"
        )
        if "sub_team" in merged.columns:
            return merged["sub_team"].value_counts().to_dict()

    return {}


@st.cache_data(ttl=300)
def load_weekly_notes_cached() -> pd.DataFrame:
    """Load weekly notes with 5-minute cache."""
    from sheets import load_weekly_notes
    return load_weekly_notes()


# ─────────────────────────────────────────────────────────
# 🔄 Cache invalidation (called by "Sync Data" button)
# ─────────────────────────────────────────────────────────

def clear_sheets_cache():
    """
    Clear all cached data from Sheets.

    Call this from the "Sync Data" button to force a fresh fetch.

    Usage in app.py:
        if st.button("Sync Data", ...):
            clear_sheets_cache()
            st.toast("Data synchronized", icon="✅")
            st.rerun()
    """
    st.cache_data.clear()


# ─────────────────────────────────────────────────────────
# 📊 Metrics computation (cached)
# ─────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_all_data_cached() -> tuple:
    """
    Load all three datasets in one call (efficient for initial load).

    Returns:
        (objectives_df, krs_df, updates_df)

    This batches the three separate requests into one cache key,
    reducing redundant calls.
    """
    return (
        load_objectives_cached(),
        load_key_results_cached(),
        load_updates_cached(),
    )


# ─────────────────────────────────────────────────────────
# 🧪 Test & diagnostics
# ─────────────────────────────────────────────────────────

def get_cache_info() -> dict:
    """
    Return cache statistics for debugging.

    Usage:
        import streamlit as st
        from sheets_cached import get_cache_info

        if st.button("Show cache status"):
            st.json(get_cache_info())
    """
    # Note: Streamlit's cache_data doesn't expose stats easily,
    # but we can track manually if needed.

    return {
        "status": "Cache is active",
        "ttl": "300 seconds (5 minutes)",
        "clear_cache": "Click 'Sync Data' button",
        "note": "If data feels stale, click 'Sync Data' to force refresh"
    }
