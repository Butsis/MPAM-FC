import streamlit as st
import pandas as pd
import base64

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="MPAM FC | Player Cards",
    page_icon="⚽",
    layout="wide",
)

# ----------------------------------------------------------------------------
# Theme: orange & black
# ----------------------------------------------------------------------------
ORANGE = "#FF7A00"
ORANGE_DARK = "#CC6200"
BLACK = "#0d0d0d"
CARD = "#161616"

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {BLACK}; }}

    .center-header {{
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        margin-bottom: 0.6rem;
    }}
    .center-header img {{
        height: 90px;
        margin-bottom: 0.4rem;
    }}
    .team-sub {{
        color: #b5b5b5;
        margin: 0;
        font-size: 0.9rem;
        letter-spacing: 0.03em;
    }}
    .matchup {{
        color: {ORANGE};
        margin: 0.3rem 0 0.1rem 0;
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: 0.02em;
    }}

    .section-title {{
        color: {ORANGE};
        font-size: 1.05rem;
        font-weight: 700;
        margin-top: 1.3rem;
        margin-bottom: 0.4rem;
        border-bottom: 2px solid {ORANGE_DARK};
        padding-bottom: 0.3rem;
    }}

    .stat-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 0.5rem;
    }}
    .stat-table td {{
        padding: 0.45rem 0.7rem;
        border-bottom: 1px solid #2a2a2a;
        color: #e5e5e5;
        font-size: 0.92rem;
    }}
    .stat-table td.label {{
        color: #a3a3a3;
    }}
    .stat-table td.value {{
        text-align: right;
        font-weight: 700;
        color: {ORANGE};
    }}
    .stat-table tr:last-child td {{
        border-bottom: none;
    }}

    .headline-card {{
        background-color: {CARD};
        border: 1px solid #2a2a2a;
        border-left: 4px solid {ORANGE};
        border-radius: 8px;
        padding: 0.7rem 1rem;
        text-align: center;
    }}
    .headline-value {{
        font-size: 1.35rem;
        font-weight: 800;
        color: {ORANGE};
    }}
    .headline-label {{
        font-size: 0.72rem;
        color: #a3a3a3;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    section[data-testid="stSidebar"] {{
        background-color: #111111;
        border-right: 1px solid {ORANGE_DARK};
    }}
    .sidebar-logo {{
        display: flex;
        justify-content: center;
        margin-bottom: 0.6rem;
    }}
    .sidebar-logo img {{
        height: 60px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_logo_base64():
    with open("mpam_logo.png", "rb") as f:
        return base64.b64encode(f.read()).decode()


LOGO_B64 = get_logo_base64()

# The Excel filename itself encodes the competition and the opponent, e.g.
# "Στατιστικα Αγωνα - Playoffs - Φοινικας Τουμπας.xlsx" -> competition is
# "Playoffs", opponent is "Φοινικας Τουμπας". Update this constant whenever
# you swap in a new match's file.
EXCEL_FILENAME = "Στατιστικα Αγωνα - Playoffs - Φοινικας Τουμπας.xlsx"
TEAM_NAME = "MPAM FC"


def parse_match_info(filename):
    """Pull competition + opponent name out of the '<prefix> - <competition> - <opponent>.xlsx' filename."""
    stem = filename.rsplit(".", 1)[0]
    parts = [p.strip() for p in stem.split(" - ")]
    if len(parts) >= 3:
        competition = parts[1]
        opponent = parts[2]
    else:
        competition, opponent = "", ""
    return competition, opponent


@st.cache_data
def load_match_meta():
    """Read Sheet1 to find whether we played at home ('Εντος') or away, and build the matchup string."""
    sheet1 = pd.read_excel(EXCEL_FILENAME, sheet_name="Sheet1")
    location_raw = ""
    if "Location" in sheet1.columns and sheet1["Location"].notna().any():
        location_raw = str(sheet1["Location"].dropna().iloc[0]).strip()
    is_home = location_raw == "Εντος"

    competition, opponent = parse_match_info(EXCEL_FILENAME)

    if is_home:
        matchup = f"{TEAM_NAME} vs {opponent}"
    else:
        matchup = f"{opponent} vs {TEAM_NAME}"

    return matchup, competition


MATCHUP, COMPETITION = load_match_meta()

# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel(
        EXCEL_FILENAME,
        sheet_name="Sheet2",
    )
    # The first column header looks like "NAME" but is actually typed with
    # Greek lookalike letters in the source file, so rename it explicitly.
    df = df.rename(columns={df.columns[0]: "NAME"})
    df = df[df["NAME"].notna()].copy()
    text_cols = ["NAME", "POSITION", "Playing Type", "Opponent", "Competition", "Outcome"]
    for col in df.columns:
        if col not in text_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

df = load_data()

PLAYING_TYPE_LABELS = {
    "Βασικος": "Starter",
    "Αλλαγη": "Substitute",
}

# ----------------------------------------------------------------------------
# Sidebar: logo (top-left) + player filter
# ----------------------------------------------------------------------------
st.sidebar.markdown(
    f'<div class="sidebar-logo"><img src="data:image/png;base64,{LOGO_B64}"></div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown("### 🔍 Select Player")
player_names = sorted(df["NAME"].unique().tolist())
selected_player = st.sidebar.selectbox("Player", player_names)

opp = df.loc[df["NAME"] == selected_player, "Opponent"].values
outcome = df.loc[df["NAME"] == selected_player, "Outcome"].values
if len(opp) and pd.notna(opp[0]):
    st.sidebar.markdown(f"**Opponent:** {opp[0]}")
if len(outcome) and pd.notna(outcome[0]):
    st.sidebar.markdown(f"**Result:** {outcome[0]}")

st.sidebar.markdown("---")
st.sidebar.caption("Open this app on your phone and bookmark it for quick access after every match.")

row = df[df["NAME"] == selected_player].iloc[0]
is_gk = str(row["POSITION"]).strip().upper() == "GK"

# ----------------------------------------------------------------------------
# Center header: logo + subtitle, above player name
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="center-header">
        <img src="data:image/png;base64,{LOGO_B64}">
        <p class="matchup">{MATCHUP}</p>
        <p class="team-sub">{COMPETITION} · Player Review</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Helper to render a simple label/value table (no charts, no bars)
# ----------------------------------------------------------------------------
def stat_table(pairs):
    """pairs: list of (label, value) tuples"""
    rows_html = "".join(
        f'<tr><td class="label">{label}</td><td class="value">{value}</td></tr>'
        for label, value in pairs
    )
    st.markdown(f'<table class="stat-table">{rows_html}</table>', unsafe_allow_html=True)


def pct(won, total):
    return f"{(won / total * 100):.0f}%" if total > 0 else "—"


def fmt(n):
    return f"{int(n)}" if float(n).is_integer() else f"{n}"

# ----------------------------------------------------------------------------
# Player header
# ----------------------------------------------------------------------------
st.markdown(f"## {row['NAME']}")
st.markdown(f"**Position:** {row['POSITION']}")

playing_type_raw = str(row["Playing Type"]).strip()
playing_type_label = PLAYING_TYPE_LABELS.get(playing_type_raw, playing_type_raw)

c1, c2, c3, c4 = st.columns(4)
headline = [
    (c1, "Minutes", fmt(row["MINUTES"])),
    (c2, "Goals", fmt(row["GOAL"])),
    (c3, "Assists", fmt(row["ASSISTS"])),
    (c4, "Playing Type", playing_type_label),
]
for col, label, value in headline:
    col.markdown(
        f'<div class="headline-card"><div class="headline-value">{value}</div>'
        f'<div class="headline-label">{label}</div></div>',
        unsafe_allow_html=True,
    )

# ----------------------------------------------------------------------------
# Shooting
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">🎯 Shooting</div>', unsafe_allow_html=True)
stat_table([
    ("Inside Shots On Target", fmt(row["INSIDE ON TARGET"])),
    ("Inside Shots Off Target", fmt(row["INSIDE OFF TARGET"])),
    ("Inside Shots Blocked", fmt(row["INSIDE BLOCKED"])),
    ("Outside Shots On Target", fmt(row["OUTSIDE ON TARGET"])),
    ("Outside Shots Off Target", fmt(row["OUTSIDE OFF TARGET"])),
    ("Outside Shots Blocked", fmt(row["OUTSIDE BLOCKED"])),
])

# ----------------------------------------------------------------------------
# Creativity (chance creation)
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">✨ Creativity</div>', unsafe_allow_html=True)
stat_table([
    ("Key Passes", fmt(row["KEY PASSES"])),
    ("Big Chances Created", fmt(row["BIG CHANCES CREATED"])),
    ("Big Chances Scored", fmt(row["BIG CHANCES SCORED"])),
    ("Big Chances Missed", fmt(row["BIG CHANCES MISSED"])),
])

# ----------------------------------------------------------------------------
# Duels
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">🥊 Duels</div>', unsafe_allow_html=True)
stat_table([
    ("Offensive Duels", f'{fmt(row["OFFENSIVE DUELS WON"])} / {fmt(row["TOTAL OFFENSIVE DUELS"])} won ({pct(row["OFFENSIVE DUELS WON"], row["TOTAL OFFENSIVE DUELS"])})'),
    ("Defensive Duels", f'{fmt(row["DEFENSIVE DUELS WON"])} / {fmt(row["TOTAL DEFENSIVE DUELS"])} won ({pct(row["DEFENSIVE DUELS WON"], row["TOTAL DEFENSIVE DUELS"])})'),
    ("Aerial Duels", f'{fmt(row["AERIAL DUES WON"])} / {fmt(row["TOTAL AERIAL DUELS"])} won ({pct(row["AERIAL DUES WON"], row["TOTAL AERIAL DUELS"])})'),
    ("Post-Duel Actions", f'{fmt(row["POST-DUEL ACTIONS SUCCESS"])} / {fmt(row["TOTAL POST-DUEL ACTIONS"])} success ({pct(row["POST-DUEL ACTIONS SUCCESS"], row["TOTAL POST-DUEL ACTIONS"])})'),
    ("Second Balls", f'{fmt(row["SECOND BALLS WON"])} won / {fmt(row["SECOND BALLS LOST"])} lost'),
    ("Long Balls", f'{fmt(row["SUCCESSFUL LONG BALLS"])} / {fmt(row["TOTAL LONG BALLS"])} successful ({pct(row["SUCCESSFUL LONG BALLS"], row["TOTAL LONG BALLS"])})'),
])

# ----------------------------------------------------------------------------
# Possession
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">⚠️ Possession Lost & Recovered</div>', unsafe_allow_html=True)
poss_col1, poss_col2 = st.columns(2)
with poss_col1:
    stat_table([
        ("Lost — Own Half", fmt(row["POSSESION LOST OWN HALF"])),
        ("...led to opp. shot", fmt(row["POSSESSION LOST OWN HALF LED TO A SHOT"])),
        ("Lost — Opp. Half", fmt(row["POSSESSION LOST OPPs HALF"])),
        ("...led to opp. shot", fmt(row["POSSESSION LOST OPPs HALF LED TO A SHOT"])),
    ])
with poss_col2:
    stat_table([
        ("Recovered — Own Half", fmt(row["BALL RECOVERY OWN HALF"])),
        ("...led to our shot", fmt(row["BALL RECOVERY OWN HALF LED TO A SHOT"])),
        ("Recovered — Opp. Half", fmt(row["BALL RECOVERY OPPs HALF"])),
        ("...led to our shot", fmt(row["BALL RECOVERY OPPs HALF LED TO A SHOT"])),
    ])

# ----------------------------------------------------------------------------
# Defensive & discipline
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">🛡️ Defensive & Discipline</div>', unsafe_allow_html=True)
def_col1, def_col2 = st.columns(2)
with def_col1:
    stat_table([
        ("Clearances", fmt(row["CLEARANCES"])),
        ("Interceptions", fmt(row["INTERCEPTIONS"])),
    ])
with def_col2:
    stat_table([
        ("Fouls Won", fmt(row["FOULS WON"])),
        ("Fouls Committed", fmt(row["FOULS COMMITED"])),
        ("Yellow Cards", fmt(row["YELLOW CARDS"])),
        ("Red Cards", fmt(row["RED CARDS"])),
    ])

# ----------------------------------------------------------------------------
# Goalkeeper
# ----------------------------------------------------------------------------
if is_gk:
    st.markdown('<div class="section-title">🧤 Goalkeeper</div>', unsafe_allow_html=True)
    stat_table([
        ("Saves", fmt(row["SAVES"])),
        ("Big Chances Saved", fmt(row["BIG CHANCES SAVED"])),
        ("Goals Conceded", fmt(row["GOALS CONCEDED"])),
    ])

st.markdown("---")
st.caption("MPAM FC · Player Review Dashboard")
