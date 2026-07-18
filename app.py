import glob
import os
import base64

import streamlit as st
import pandas as pd

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
TEAM_NAME = "MPAM FC"

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

PLAYING_TYPE_LABELS = {
    "Βασικος": "Starter",
    "Αλλαγη": "Substitute",
}

# Columns that describe a player-row (not a stat to add up across matches)
NON_STAT_COLS = [
    "NAME", "POSITION", "Playing Type", "Opponent", "Competition",
    "Outcome", "Round", "Game ID", "__match_id", "__matchup", "__date",
]

# ----------------------------------------------------------------------------
# Discover every match workbook sitting next to this app, and load them all
# ----------------------------------------------------------------------------
def discover_match_files():
    files = [f for f in glob.glob("*.xlsx") if not os.path.basename(f).startswith("~$")]
    return sorted(files)


def _files_fingerprint():
    """Cache-busting key: changes whenever a file is added, removed, or edited."""
    return tuple((f, os.path.getmtime(f)) for f in discover_match_files())


@st.cache_data
def load_all_matches(fingerprint):
    match_files = [f for f, _ in fingerprint]
    player_frames = []
    match_meta = []
    skipped = []

    for f in match_files:
        try:
            sheet1 = pd.read_excel(f, sheet_name="Sheet1")
            sheet2 = pd.read_excel(f, sheet_name="Sheet2")
        except Exception:
            skipped.append(f)
            continue

        # The first column header looks like "NAME" but is typed with Greek
        # lookalike letters in the source file, so rename it explicitly.
        sheet2 = sheet2.rename(columns={sheet2.columns[0]: "NAME"})
        sheet2 = sheet2[sheet2["NAME"].notna()].copy()
        if sheet2.empty:
            skipped.append(f)
            continue

        text_cols = ["NAME", "POSITION", "Playing Type", "Opponent", "Competition", "Outcome"]
        for col in sheet2.columns:
            if col not in text_cols:
                sheet2[col] = pd.to_numeric(sheet2[col], errors="coerce").fillna(0)

        game_id = sheet2["Game ID"].iloc[0] if "Game ID" in sheet2.columns else f
        opponent = str(sheet2["Opponent"].iloc[0]) if "Opponent" in sheet2.columns else "Unknown"
        competition = str(sheet2["Competition"].iloc[0]) if "Competition" in sheet2.columns else ""

        location_raw = ""
        if "Location" in sheet1.columns and sheet1["Location"].notna().any():
            location_raw = str(sheet1["Location"].dropna().iloc[0]).strip()
        is_home = location_raw == "Εντος"

        date_val = None
        if "Date" in sheet1.columns and sheet1["Date"].notna().any():
            date_val = pd.to_datetime(sheet1["Date"].dropna().iloc[0])

        matchup = f"{TEAM_NAME} vs {opponent}" if is_home else f"{opponent} vs {TEAM_NAME}"

        sheet2["__match_id"] = game_id
        sheet2["__matchup"] = matchup
        sheet2["__date"] = date_val

        player_frames.append(sheet2)
        match_meta.append({
            "match_id": game_id,
            "file": f,
            "matchup": matchup,
            "competition": competition,
            "opponent": opponent,
            "date": date_val,
        })

    if not player_frames:
        return pd.DataFrame(), [], skipped

    combined = pd.concat(player_frames, ignore_index=True)
    match_meta.sort(key=lambda m: m["date"] if m["date"] is not None else pd.Timestamp.min, reverse=True)
    return combined, match_meta, skipped


combined_df, matches, skipped_files = load_all_matches(_files_fingerprint())

if combined_df.empty:
    st.error("No match files found. Add at least one .xlsx match export to this app's folder.")
    st.stop()


def match_label(m):
    date_str = m["date"].strftime("%d %b %Y") if m["date"] is not None else "date n/a"
    return f'{m["matchup"]} — {m["competition"]} ({date_str})'


# ----------------------------------------------------------------------------
# Sidebar: logo (top-left), match filter, player filter
# ----------------------------------------------------------------------------
st.sidebar.markdown(
    f'<div class="sidebar-logo"><img src="data:image/png;base64,{LOGO_B64}"></div>',
    unsafe_allow_html=True,
)

st.sidebar.markdown("### 🗓️ Select Match")
match_option_labels = [match_label(m) for m in matches] + ["All Games"]
selected_match_label = st.sidebar.selectbox("Match", match_option_labels, index=0)

if selected_match_label == "All Games":
    selected_match_id = "ALL"
    selected_match_meta = None
else:
    selected_idx = match_option_labels.index(selected_match_label)
    selected_match_meta = matches[selected_idx]
    selected_match_id = selected_match_meta["match_id"]

st.sidebar.markdown("### 🔍 Select Player")
if selected_match_id == "ALL":
    scoped_df = combined_df
else:
    scoped_df = combined_df[combined_df["__match_id"] == selected_match_id]

player_names = sorted(scoped_df["NAME"].unique().tolist())

if "selected_player" not in st.session_state:
    st.session_state["selected_player"] = player_names[0] if player_names else None

# Keep the previously selected player highlighted if they're in this match's
# roster too; only fall back to the first player when they aren't (e.g. they
# didn't play in the newly selected match).
if st.session_state["selected_player"] in player_names:
    default_index = player_names.index(st.session_state["selected_player"])
else:
    default_index = 0

selected_player = st.sidebar.selectbox("Player", player_names, index=default_index)
st.session_state["selected_player"] = selected_player

if selected_match_id != "ALL":
    st.sidebar.markdown(f"**Opponent:** {selected_match_meta['opponent']}")
else:
    st.sidebar.markdown(f"**{len(matches)} matches loaded**")

if skipped_files:
    st.sidebar.caption(f"⚠️ Skipped unreadable files: {', '.join(skipped_files)}")

st.sidebar.markdown("---")
st.sidebar.caption("Open this app on your phone and bookmark it for quick access after every match.")

# ----------------------------------------------------------------------------
# Build the row of stats to display: single match, or season aggregate
# ----------------------------------------------------------------------------
is_all_games = selected_match_id == "ALL"

if is_all_games:
    player_history = combined_df[combined_df["NAME"] == selected_player].sort_values("__date", ascending=False)
    stat_cols = [c for c in player_history.columns if c not in NON_STAT_COLS]
    row = player_history[stat_cols].sum()
    position_mode = player_history["POSITION"].mode()
    row["POSITION"] = position_mode.iat[0] if not position_mode.empty else player_history["POSITION"].iloc[0]
    matches_played = player_history["__match_id"].nunique()
else:
    player_row_df = scoped_df[scoped_df["NAME"] == selected_player]
    row = player_row_df.iloc[0]
    matches_played = 1

is_gk = str(row["POSITION"]).strip().upper() == "GK"

# ----------------------------------------------------------------------------
# Center header: logo + matchup / season info, above player name
# ----------------------------------------------------------------------------
if is_all_games:
    line1 = "All Games"
    line2 = f"{len(matches)} Matches · Season Review"
else:
    line1 = selected_match_meta["matchup"]
    line2 = f'{selected_match_meta["competition"]} · Player Review'

st.markdown(
    f"""
    <div class="center-header">
        <img src="data:image/png;base64,{LOGO_B64}">
        <p class="matchup">{line1}</p>
        <p class="team-sub">{line2}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Helpers
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
# Player header + headline boxes
# ----------------------------------------------------------------------------
st.markdown(f"## {selected_player}")
st.markdown(f"**Position:** {row['POSITION']}")

c1, c2, c3, c4 = st.columns(4)
if is_all_games:
    headline = [
        (c1, "Matches Played", fmt(matches_played)),
        (c2, "Minutes", fmt(row["MINUTES"])),
        (c3, "Goals", fmt(row["GOAL"])),
        (c4, "Assists", fmt(row["ASSISTS"])),
    ]
else:
    playing_type_raw = str(row["Playing Type"]).strip()
    playing_type_label = PLAYING_TYPE_LABELS.get(playing_type_raw, playing_type_raw)
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
# Match-by-match breakdown (All Games mode only) — see every game at once
# ----------------------------------------------------------------------------
if is_all_games:
    st.markdown('<div class="section-title">📅 Match-by-Match</div>', unsafe_allow_html=True)
    breakdown = pd.DataFrame({
        "Date": player_history["__date"].dt.strftime("%d %b %Y"),
        "Match": player_history["__matchup"],
        "Competition": player_history["Competition"],
        "Result": player_history["Outcome"],
        "Started": player_history["Playing Type"].map(PLAYING_TYPE_LABELS).fillna(player_history["Playing Type"]),
        "Minutes": player_history["MINUTES"].astype(int),
        "Goals": player_history["GOAL"].astype(int),
        "Assists": player_history["ASSISTS"].astype(int),
    })
    st.dataframe(breakdown, hide_index=True, use_container_width=True)

# ----------------------------------------------------------------------------
# Shooting
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">🎯 Shooting</div>', unsafe_allow_html=True)
shoot_col1, shoot_col2 = st.columns(2)
with shoot_col1:
    st.markdown("**Inside the Box**")
    stat_table([
        ("Shots On Target", fmt(row["INSIDE ON TARGET"])),
        ("Shots Off Target", fmt(row["INSIDE OFF TARGET"])),
        ("Shots Blocked", fmt(row["INSIDE BLOCKED"])),
    ])
with shoot_col2:
    st.markdown("**Outside the Box**")
    stat_table([
        ("Shots On Target", fmt(row["OUTSIDE ON TARGET"])),
        ("Shots Off Target", fmt(row["OUTSIDE OFF TARGET"])),
        ("Shots Blocked", fmt(row["OUTSIDE BLOCKED"])),
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
    ("Long Balls", f'{fmt(row["SUCCESSFUL LONG BALLS"])} / {fmt(row["TOTAL LONG BALLS"])} successful ({pct(row["SUCCESSFUL LONG BALLS"], row["TOTAL LONG BALLS"])})'),
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
])

# ----------------------------------------------------------------------------
# Possession
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">⚠️ Possession Lost & Recovered</div>', unsafe_allow_html=True)
poss_col1, poss_col2 = st.columns(2)
with poss_col1:
    stat_table([
        ("Possession Lost — Own Half", fmt(row["POSSESION LOST OWN HALF"])),
        ("Possession Lost — Own Half Led to Opponent Shot", fmt(row["POSSESSION LOST OWN HALF LED TO A SHOT"])),
        ("Possession Lost — Opponent's Half", fmt(row["POSSESSION LOST OPPs HALF"])),
        ("Possession Lost — Opponent's Half Led to Opponent Shot", fmt(row["POSSESSION LOST OPPs HALF LED TO A SHOT"])),
    ])
with poss_col2:
    stat_table([
        ("Ball Recovery — Own Half", fmt(row["BALL RECOVERY OWN HALF"])),
        ("Ball Recovery — Own Half Led to Our Shot", fmt(row["BALL RECOVERY OWN HALF LED TO A SHOT"])),
        ("Ball Recovery — Opponent's Half", fmt(row["BALL RECOVERY OPPs HALF"])),
        ("Ball Recovery — Opponent's Half Led to Our Shot", fmt(row["BALL RECOVERY OPPs HALF LED TO A SHOT"])),
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
