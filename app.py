import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="MPAM FC | Player Cards",
    page_icon="⚽",
    layout="wide",
)

# ----------------------------------------------------------------------------
# Style
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; }
    .team-header {
        background: linear-gradient(90deg, #1a3d1a 0%, #0e1117 100%);
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.2rem;
        border: 1px solid #2e5a2e;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 0.8rem;
        text-align: center;
    }
    .metric-value { font-size: 1.6rem; font-weight: 700; color: #4ade80; }
    .metric-label { font-size: 0.75rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel(
        "Στατιστικα Αγωνα - Playoffs - Φοινικας Τουμπας.xlsx",
        sheet_name="Sheet2",
    )
    # The first column header looks like "NAME" but is actually typed with
    # Greek lookalike letters in the source file, so rename it explicitly.
    df = df.rename(columns={df.columns[0]: "NAME"})
    df = df[df["NAME"].notna()].copy()
    # numeric columns -> fill NaN with 0 for stat math, keep name/position/text cols aside
    text_cols = ["NAME", "POSITION", "Playing Type", "Opponent", "Competition", "Outcome"]
    for col in df.columns:
        if col not in text_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

df = load_data()

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown(
    """
    <div class="team-header">
        <h1 style="margin:0; color:#f0f0f0;">⚽ MPAM FC — Player Cards</h1>
        <p style="margin:0; color:#a0a0a0;">Match statistics dashboard · Playoffs</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Sidebar - player filter
# ----------------------------------------------------------------------------
st.sidebar.header("🔍 Select Player")
player_names = sorted(df["NAME"].unique().tolist())
selected_player = st.sidebar.selectbox("Player", player_names)

if len(df["Opponent"].dropna().unique()) > 0:
    opp = df.loc[df["NAME"] == selected_player, "Opponent"].values
    outcome = df.loc[df["NAME"] == selected_player, "Outcome"].values
    if len(opp) and pd.notna(opp[0]):
        st.sidebar.markdown(f"**Opponent:** {opp[0]}")
    if len(outcome) and pd.notna(outcome[0]):
        st.sidebar.markdown(f"**Result:** {outcome[0]}")

st.sidebar.markdown("---")
st.sidebar.caption("Tip: open this app on your phone and bookmark it for quick access to your stats after every match.")

row = df[df["NAME"] == selected_player].iloc[0]
is_gk = str(row["POSITION"]).strip().upper() == "GK"

# ----------------------------------------------------------------------------
# Player card header
# ----------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
with c1:
    st.markdown(f"## {row['NAME']}")
    st.markdown(f"**Position:** {row['POSITION']}")
with c2:
    st.markdown('<div class="metric-card"><div class="metric-value">%d</div><div class="metric-label">Minutes</div></div>' % row['MINUTES'], unsafe_allow_html=True)
with c3:
    st.markdown('<div class="metric-card"><div class="metric-value">%d</div><div class="metric-label">Goals</div></div>' % row['GOAL'], unsafe_allow_html=True)
with c4:
    st.markdown('<div class="metric-card"><div class="metric-value">%d</div><div class="metric-label">Assists</div></div>' % row['ASSISTS'], unsafe_allow_html=True)

st.markdown("### ")

# ----------------------------------------------------------------------------
# Duels chart
# ----------------------------------------------------------------------------
st.subheader("🥊 Duels")

duel_categories = ["Offensive", "Defensive", "Aerial"]
duel_total = [row["TOTAL OFFENSIVE DUELS"], row["TOTAL DEFENSIVE DUELS"], row["TOTAL AERIAL DUELS"]]
duel_won = [row["OFFENSIVE DUELS WON"], row["DEFENSIVE DUELS WON"], row["AERIAL DUES WON"]]
duel_lost = [t - w for t, w in zip(duel_total, duel_won)]

fig_duels = go.Figure()
fig_duels.add_trace(go.Bar(
    name="Won", x=duel_categories, y=duel_won,
    marker_color="#4ade80", text=duel_won, textposition="auto",
))
fig_duels.add_trace(go.Bar(
    name="Lost", x=duel_categories, y=duel_lost,
    marker_color="#f87171", text=duel_lost, textposition="auto",
))
fig_duels.update_layout(
    barmode="stack",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#e5e7eb",
    height=350,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=30, b=20),
)
st.plotly_chart(fig_duels, use_container_width=True)

duel_cols = st.columns(3)
for i, cat in enumerate(duel_categories):
    win_rate = (duel_won[i] / duel_total[i] * 100) if duel_total[i] > 0 else 0
    duel_cols[i].metric(f"{cat} duel win rate", f"{win_rate:.0f}%", f"{int(duel_won[i])}/{int(duel_total[i])}")

# ----------------------------------------------------------------------------
# Possession lost / recovered chart
# ----------------------------------------------------------------------------
st.subheader("⚠️ Possession Lost vs Recovered")

pcol1, pcol2 = st.columns(2)

with pcol1:
    lost_labels = ["Own Half", "Opp. Half"]
    lost_values = [row["POSSESION LOST OWN HALF"], row["POSSESSION LOST OPPs HALF"]]
    lost_led_to_shot = [row["POSSESSION LOST OWN HALF LED TO A SHOT"], row["POSSESSION LOST OPPs HALF LED TO A SHOT"]]

    fig_lost = go.Figure()
    fig_lost.add_trace(go.Bar(
        name="Possession Lost", x=lost_labels, y=lost_values,
        marker_color="#fb923c", text=lost_values, textposition="auto",
    ))
    fig_lost.add_trace(go.Bar(
        name="...led to opp. shot", x=lost_labels, y=lost_led_to_shot,
        marker_color="#dc2626", text=lost_led_to_shot, textposition="auto",
    ))
    fig_lost.update_layout(
        barmode="group",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        height=320,
        title="Possession Lost",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=20),
    )
    st.plotly_chart(fig_lost, use_container_width=True)

with pcol2:
    rec_labels = ["Own Half", "Opp. Half"]
    rec_values = [row["BALL RECOVERY OWN HALF"], row["BALL RECOVERY OPPs HALF"]]
    rec_led_to_shot = [row["BALL RECOVERY OWN HALF LED TO A SHOT"], row["BALL RECOVERY OPPs HALF LED TO A SHOT"]]

    fig_rec = go.Figure()
    fig_rec.add_trace(go.Bar(
        name="Ball Recovery", x=rec_labels, y=rec_values,
        marker_color="#38bdf8", text=rec_values, textposition="auto",
    ))
    fig_rec.add_trace(go.Bar(
        name="...led to our shot", x=rec_labels, y=rec_led_to_shot,
        marker_color="#4ade80", text=rec_led_to_shot, textposition="auto",
    ))
    fig_rec.update_layout(
        barmode="group",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        height=320,
        title="Ball Recovery",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=20),
    )
    st.plotly_chart(fig_rec, use_container_width=True)

# ----------------------------------------------------------------------------
# Attacking output
# ----------------------------------------------------------------------------
st.subheader("🎯 Attacking Output")

shots_labels = ["Inside On", "Inside Off", "Inside Blocked", "Outside On", "Outside Off", "Outside Blocked"]
shots_values = [
    row["INSIDE ON TARGET"], row["INSIDE OFF TARGET"], row["INSIDE BLOCKED"],
    row["OUTSIDE ON TARGET"], row["OUTSIDE OFF TARGET"], row["OUTSIDE BLOCKED"],
]
fig_shots = go.Figure(go.Bar(
    x=shots_labels, y=shots_values,
    marker_color=["#4ade80", "#facc15", "#94a3b8", "#4ade80", "#facc15", "#94a3b8"],
    text=shots_values, textposition="auto",
))
fig_shots.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#e5e7eb",
    height=320,
    margin=dict(t=20, b=20),
)
st.plotly_chart(fig_shots, use_container_width=True)

att_cols = st.columns(4)
att_cols[0].metric("Key Passes", int(row["KEY PASSES"]))
att_cols[1].metric("Big Chances Created", int(row["BIG CHANCES CREATED"]))
att_cols[2].metric("Big Chances Scored", int(row["BIG CHANCES SCORED"]))
att_cols[3].metric("Big Chances Missed", int(row["BIG CHANCES MISSED"]))

# ----------------------------------------------------------------------------
# Defensive & discipline
# ----------------------------------------------------------------------------
st.subheader("🛡️ Defensive Actions & Discipline")

def_cols = st.columns(6)
def_cols[0].metric("Clearances", int(row["CLEARANCES"]))
def_cols[1].metric("Interceptions", int(row["INTERCEPTIONS"]))
def_cols[2].metric("Fouls Won", int(row["FOULS WON"]))
def_cols[3].metric("Fouls Committed", int(row["FOULS COMMITED"]))
def_cols[4].metric("Yellow Cards", int(row["YELLOW CARDS"]))
def_cols[5].metric("Red Cards", int(row["RED CARDS"]))

# ----------------------------------------------------------------------------
# Goalkeeper section
# ----------------------------------------------------------------------------
if is_gk:
    st.subheader("🧤 Goalkeeper Stats")
    gk_cols = st.columns(3)
    gk_cols[0].metric("Saves", int(row["SAVES"]))
    gk_cols[1].metric("Big Chances Saved", int(row["BIG CHANCES SAVED"]))
    gk_cols[2].metric("Goals Conceded", int(row["GOALS CONCEDED"]))

# ----------------------------------------------------------------------------
# Raw stats table (expandable)
# ----------------------------------------------------------------------------
with st.expander("📋 View full raw stats for this player"):
    display_row = row.drop(labels=["Playing Type", "Opponent", "Competition", "Outcome", "Round", "Game ID"], errors="ignore")
    st.dataframe(display_row.astype(str), use_container_width=True)

st.markdown("---")
st.caption("MPAM FC · Player Cards Dashboard · Data from match statistics export")