import pandas as pd
import streamlit as st

from ui.components.auth_guard import require_auth


def render():
    require_auth()

    st.header("⭐ My Saved Events")

    api = st.session_state["api"]
    data = api.get_saved_events(limit=500)
    items = data.get("items", [])

    if not items:
        st.info("You haven't saved any events yet. Go to the Feed page and save some!")
        return

    df = pd.DataFrame(items)

    st.caption(f"Total saved: {data.get('total', 0)}")

    # ── Table with delete buttons ─────────────────────────────────────────────

    for i, row in df.iterrows():
        col_info, col_btn = st.columns([5, 1])
        with col_info:
            note_text = f" — _{row.get('note')}_" if row.get("note") else ""
            st.write(f"**{row['event_id']}**{note_text}")
        with col_btn:
            if st.button("🗑️", key=f"del_saved_{i}"):
                if api.delete_saved_event(row["event_id"]):
                    st.success(f"Removed {row['event_id']}")
                    st.rerun()
                else:
                    st.error("Failed to remove.")
