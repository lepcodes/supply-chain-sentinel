import pandas as pd
import streamlit as st

from sentinel.news_scoring import get_all_news

# 1. Page Config: Keep it wide, add an icon
st.set_page_config(layout="wide", page_title="Sentinel", page_icon="🛡️")

# 2. Custom CSS for "Badges" (Make the scores look good)
st.markdown(
    """
<style>
    .score-badge {
        padding: 4px 8px;
        border-radius: 4px;
        color: white;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)


# 3. Helper Functions
def get_color(score):
    if score >= 80:
        return "#dc3545"  # Red (Critical)
    if score >= 50:
        return "#ffc107"  # Yellow (Warning)
    return "#28a745"  # Green (Safe/Low)


def get_emoji(score):
    if score >= 80:
        return "🚨"
    if score >= 50:
        return "⚠️"
    return "ℹ️"


# 4. Data Loading (Cached for performance, cleared on refresh)
def load_data():
    rows = get_all_news("data/database.db")
    df = pd.DataFrame(
        rows, columns=["id", "Title", "Link", "Published", "Text", "Relevance"]
    )
    # CRITICAL: Sort by Relevance DESCENDING. Show the fire first.
    return df.sort_values(by="Relevance", ascending=False)


# Sidebar: Control Center
st.sidebar.title("🛡️ Sentinel Config")
min_score = st.sidebar.slider("Minimum Relevance Score", 0, 100, 50)
if st.sidebar.button("Refresh Feed"):
    st.rerun()

# Main UI
st.title("Supply Chain Threat Monitor")

# Get Data
df = load_data()
filtered_df = df[df["Relevance"] >= min_score]

# Top KPI Row (The "At a Glance" view)
col1, col2, col3 = st.columns(3)
col1.metric("Active Threats", len(filtered_df))
col2.metric("Critical Risks (80+)", len(df[df["Relevance"] >= 80]))
col3.metric("Highest Risk Score", df["Relevance"].max())

st.divider()

# The Feed
for index, row in filtered_df.iterrows():
    score = row["Relevance"]
    color = get_color(score)
    emoji = get_emoji(score)

    # Use an Expander: Title is visible, Details are hidden
    # We color-code the title visually using specific formatting if needed,
    # but for now, the emoji + score is the signal.
    with st.expander(f"{emoji} [{score}] {row['Title']}"):
        # Inside the card
        c1, c2 = st.columns([3, 1])

        with c1:
            st.markdown("**Summary:**")
            # Show snippet, not wall of text
            snippet = row["Text"][:300] + "..." if row["Text"] else "No text content."
            st.caption(snippet)

        with c2:
            st.markdown("**Relevance:**")
            # HTML Badge
            st.markdown(
                f'<div class="score-badge" style="background-color: {color}; text-align: center;">{score}/100</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**Date:** {row['Published']}")
            st.link_button("🔗 Open Source", row["Link"])
