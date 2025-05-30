
import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Dream11 GL Team Generator", layout="wide")
st.title("🏏 Dream11 Grand League (GL) Team Generator")

st.markdown("""
Easily generate up to **39 unique GL teams** with Captain & Vice-Captain logic based on your custom player pool.
Upload a CSV or manually enter players to get started.
""")

# --- Upload or create player pool ---
option = st.radio("How would you like to input your player pool?", ["Upload CSV", "Enter Manually"])

if option == "Upload CSV":
    uploaded_file = st.file_uploader("Upload CSV with columns: name, team, role (WK/BAT/AR/BOWL), rating (1-10), tags (comma separated)", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df['tags'] = df['tags'].fillna('').apply(lambda x: [tag.strip().lower() for tag in x.split(',')])
else:
    st.subheader("Manual Player Entry")
    with st.form("manual_input"):
        player_data = st.text_area("Enter players (one per line, format: name,team,role,rating,tags)")
        submit = st.form_submit_button("Create Player Pool")
        if submit:
            rows = [line.split(',') for line in player_data.split('\n') if line.strip() != ""]
            df = pd.DataFrame(rows, columns=["name", "team", "role", "rating", "tags"])
            df['rating'] = df['rating'].astype(float)
            df['tags'] = df['tags'].fillna('').apply(lambda x: [tag.strip().lower() for tag in x.split(',')])

# --- Strategy Toggles ---
st.sidebar.header("📊 Strategy Toggles")
prefer_high_rated = st.sidebar.checkbox("Prefer High-Rated Players", value=True)
strategy = st.sidebar.selectbox("Select Pitch Strategy", ["Balanced", "Spin-Friendly", "Batting Paradise", "Swinging Conditions"])

# --- Team Generation Logic ---
def is_valid(team):
    roles = {"WK": 0, "BAT": 0, "AR": 0, "BOWL": 0}
    teams = {}
    for p in team:
        roles[p["role"]] += 1
        teams[p["team"]] = teams.get(p["team"], 0) + 1
    return (1 <= roles["WK"] <= 4 and 3 <= roles["BAT"] <= 6 and
            1 <= roles["AR"] <= 4 and 3 <= roles["BOWL"] <= 6 and
            all(count <= 7 for count in teams.values()))

def apply_strategy_filter(players):
    if strategy == "Spin-Friendly":
        return [p for p in players if "spin" in p["tags"] or p["role"] in ["AR", "BOWL"]]
    elif strategy == "Batting Paradise":
        return [p for p in players if "top-order" in p["tags"] or p["role"] in ["BAT", "WK"]]
    elif strategy == "Swinging Conditions":
        return [p for p in players if "powerplay" in p["tags"] or p["role"] == "BOWL"]
    return players

def weighted_sample(players, k):
    if prefer_high_rated:
        weights = [p['rating'] for p in players]
    else:
        weights = [1] * len(players)
    return random.choices(players, weights=weights, k=k)

def generate_valid_team(players):
    attempts = 0
    while attempts < 100:
        sample_pool = apply_strategy_filter(players)
        team = weighted_sample(sample_pool, 11)
        if is_valid(team):
            return team
        attempts += 1
    return None

# --- Generate Teams Button ---
if 'df' in locals() and not df.empty:
    num_teams = st.slider("Select number of teams to generate", 1, 39, 11)

    captain_pool = st.multiselect("Select possible Captains", df['name'].tolist(), default=df['name'].tolist())
    vice_captain_pool = st.multiselect("Select possible Vice-Captains", df['name'].tolist(), default=df['name'].tolist())

    if st.button("Generate GL Teams"):
        teams = []
        used = set()
        players_list = df.to_dict(orient="records")

        while len(teams) < num_teams:
            team = generate_valid_team(players_list)
            if not team:
                break
            sorted_names = tuple(sorted([p["name"] for p in team]))
            if sorted_names in used:
                continue

            used.add(sorted_names)
            names = [p["name"] for p in team]
            valid_c = [n for n in names if n in captain_pool]
            valid_vc = [n for n in names if n in vice_captain_pool and n not in valid_c]

            captain = random.choice(valid_c) if valid_c else random.choice(names)
            vice_captain = random.choice(valid_vc) if valid_vc else random.choice([n for n in names if n != captain])

            teams.append({"players": names, "captain": captain, "vice_captain": vice_captain})

        # Team Preview Filter
        with st.expander("🔍 Team Preview Filter"):
            filter_player = st.selectbox("Filter teams containing player", ["None"] + df['name'].tolist())
            filtered_teams = [t for t in teams if filter_player == "None" or filter_player in t['players']]

            for idx, t in enumerate(filtered_teams, 1):
                st.markdown(f"### Team {idx}")
                st.markdown(
                    f"**Captain**: {t['captain']} | **Vice-Captain**: {t['vice_captain']}\n\n" +
                    f"**Players**: {', '.join(t['players'])}"
                )

        # Export to CSV
        export_df = pd.DataFrame([
            {"Team No": i+1, "Captain": t['captain'], "Vice Captain": t['vice_captain'], "Players": ", ".join(t['players'])}
            for i, t in enumerate(teams)
        ])

        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Teams as CSV", data=csv, file_name="dream11_gl_teams.csv", mime="text/csv")

else:
    st.info("Please upload or enter a valid player pool to begin.")
