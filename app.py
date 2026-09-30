import streamlit as st
import pandas as pd
import datetime
import random
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Date Night Dynamo", page_icon="✨", layout="centered")

FILE_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "activities.csv")

# Custom Dark & Cyan Styling
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    h1, h2, h3 { color: #00F2FF !important; }
    .stButton>button { 
        background-color: #00F2FF; 
        color: #000000; 
        font-weight: bold; 
        border-radius: 8px; 
        width: 100%;
        border: none;
    }
    .stButton>button:hover { background-color: #00B8C4; color: black; }
    .card {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #00F2FF;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CSV FUNCTIONS ---
def load_data():
    if not os.path.exists(FILE_NAME):
        df = pd.DataFrame(columns=["Activity", "Category", "Season", "Duration", "Cost", "Comments"])
        df.to_csv(FILE_NAME, index=False)
        return df
    return pd.read_csv(FILE_NAME).fillna("")

def save_data(df):
    df.to_csv(FILE_NAME, index=False)

def get_season(dt):
    m = dt.month
    if 3 <= m <= 5: return "Spring"
    if 6 <= m <= 8: return "Summer"
    if 9 <= m <= 11: return "Autumn"
    return "Winter"

# --- MAIN APP ---
st.title("⚡ DATE NIGHT DYNAMO")
st.caption("Plan the next adventure together")

tab1, tab2, tab3 = st.tabs(["🎲 Plan a Date", "➕ Add Activity", "📋 All Activities"])

# ================= TAB 1: RANDOMIZER =================
with tab1:
    df = load_data()
    
    col1, col2 = st.columns(2)
    with col1:
        picked_date = st.date_input("Pick a date", datetime.date.today())
    with col2:
        dur_options = ["<4hr", "<24hrs", "<48hrs", "<7days"]
        max_duration = st.selectbox("Max Time Available", dur_options)

    # Categories (Vibes)
    all_categories = sorted(list(set(df["Category"].dropna().tolist()))) if not df.empty else []
    selected_vibes = st.multiselect("Select Vibes", options=all_categories, default=all_categories)

    if st.button("🎲 GENERATE SURPRISE SCHEDULE"):
        target_season = get_season(picked_date)
        max_idx = dur_options.index(max_duration)
        allowed_durations = dur_options[:max_idx + 1]

        # Filter
        filtered = df[
            (df["Season"].isin(["Any", target_season])) &
            (df["Duration"].isin(allowed_durations)) &
            (df["Category"].isin(selected_vibes))
        ]

        if filtered.empty:
            st.warning("Nothing fits! Try picking more vibes or a longer duration.")
            st.session_state["selection"] = None
        else:
            count = 2 if (max_idx > 0 and len(filtered) > 1) else 1
            st.session_state["selection"] = filtered.sample(n=count).to_dict('records')

    # Display Results
    if "selection" in st.session_state and st.session_state["selection"]:
        st.write("---")
        st.subheader("🔥 The Plan")
        for item in st.session_state["selection"]:
            st.markdown(f"""
            <div class="card">
                <h3 style="margin:0 0 5px 0;">★ {item['Activity'].upper()}</h3>
                <p style="margin:0; color:#B0B0B0;">🏷️ {item['Category']} | ⏳ {item['Duration']} | 💰 {item['Cost']}</p>
                {"<p style='margin:5px 0 0 0;'><i>Note: " + item['Comments'] + "</i></p>" if item['Comments'] else ""}
            </div>
            """, unsafe_allow_html=True)

        if st.button("✅ Lock this in! (Remove from list)"):
            chosen_names = [x["Activity"] for x in st.session_state["selection"]]
            df = df[~df["Activity"].isin(chosen_names)]
            save_data(df)
            st.success("Locked in! Activities removed from list. Have fun! 🎉")
            st.session_state["selection"] = None
            st.rerun()

# ================= TAB 2: ADD ACTIVITY =================
with tab2:
    st.subheader("Add a New Date Idea")
    with st.form("new_activity_form", clear_on_submit=True):
        new_act = st.text_input("Activity Name*")
        new_cat = st.text_input("Category / Vibe (e.g. Places to Eat, Chilling)*")
        new_season = st.selectbox("Season", ["Any", "Spring", "Summer", "Autumn", "Winter"])
        new_dur = st.selectbox("Duration", ["<4hr", "<24hrs", "<48hrs", "<7days"])
        new_cost = st.selectbox("Cost", ["Free", "Low", "Medium", "High"])
        new_notes = st.text_area("Notes / Comments")
        
        submitted = st.form_submit_button("Add Activity")
        if submitted:
            if not new_act or not new_cat:
                st.error("Please provide both an Activity name and Category!")
            else:
                df = load_data()
                new_row = pd.DataFrame([{
                    "Activity": new_act,
                    "Category": new_cat,
                    "Season": new_season,
                    "Duration": new_dur,
                    "Cost": new_cost,
                    "Comments": new_notes
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success(f"Added '{new_act}' to the list!")

# ================= TAB 3: MANAGE / DELETE =================
with tab3:
    st.subheader("Manage Activities")
    df = load_data()
    st.dataframe(df, use_container_width=True)

    to_delete = st.selectbox("Delete an activity:", ["-- Choose one to delete --"] + sorted(df["Activity"].tolist()))
    if st.button("🗑️ Delete Selected Activity"):
        if to_delete != "-- Choose one to delete --":
            df = df[df["Activity"] != to_delete]
            save_data(df)
            st.success(f"Removed '{to_delete}'!")
            st.rerun()