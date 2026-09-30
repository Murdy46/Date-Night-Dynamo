import streamlit as st
import pandas as pd
import datetime
import random
from streamlit_gsheets import GSheetsConnection

# --- PAGE CONFIG ---
st.set_page_config(page_title="Date Night Dynamo", page_icon="✨", layout="centered")

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

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # ttl=0 ensures real-time updates when either of you edits
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["Activity", "Category", "Season", "Duration", "Cost", "Comments"])
        return df.fillna("")
    except Exception:
        return pd.DataFrame(columns=["Activity", "Category", "Season", "Duration", "Cost", "Comments"])

def save_data(df):
    conn.update(data=df)

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

    # Cost Selection
    cost_options = ["Free", "Low", "Medium", "High"]
    selected_costs = st.multiselect("Select Cost", options=cost_options, default=cost_options)

    # Categories (Vibes)
    all_categories = sorted(list(set(df["Category"].dropna().tolist()))) if not df.empty else []
    selected_vibes = st.multiselect("Select Vibes", options=all_categories, default=all_categories)

    if st.button("🎲 GENERATE SURPRISE SCHEDULE"):
        target_season = get_season(picked_date)
        max_idx = dur_options.index(max_duration)
        allowed_durations = dur_options[:max_idx + 1]

        # Filter (Now supports comma-separated seasons e.g. "Spring, Summer")
        filtered = df[
            (df["Season"].apply(lambda s: "Any" in str(s) or target_season in [x.strip() for x in str(s).split(",")])) &
            (df["Duration"].isin(allowed_durations)) &
            (df["Category"].isin(selected_vibes)) &
            (df["Cost"].isin(selected_costs))
        ]

        if filtered.empty:
            st.warning("Nothing fits! Try picking more vibes, costs, or a longer duration.")
            st.session_state["selection"] = None
        else:
            # Time budget hours and maximum items allowed
            dur_hours = {"<4hr": 4, "<24hrs": 14, "<48hrs": 36, "<7days": 100}
            max_budget = dur_hours.get(max_duration, 4)
            max_items = {"<4hr": 1, "<24hrs": 3, "<48hrs": 4, "<7days": 5}.get(max_duration, 2)

            shuffled = filtered.sample(frac=1).to_dict('records')
            selections = []
            total_hours = 0

            # Accumulate smaller activities into the longer time window
            for item in shuffled:
                item_hours = dur_hours.get(item["Duration"], 4)
                if total_hours + item_hours <= max_budget and len(selections) < max_items:
                    selections.append(item)
                    total_hours += item_hours

            st.session_state["selection"] = selections if selections else [shuffled[0]]

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
            st.success("Locked in! Activities removed from Google Sheet. Have fun! 🎉")
            st.session_state["selection"] = None
            st.rerun()

# ================= TAB 2: ADD ACTIVITY =================
with tab2:
    st.subheader("Add a New Date Idea")
    df = load_data()
    existing_cats = sorted([str(c) for c in df["Category"].dropna().unique() if str(c).strip()]) if not df.empty else []

    with st.form("new_activity_form", clear_on_submit=True):
        new_act = st.text_input("Activity Name*")
        
        # Category Dropdown + New Category Option
        cat_choice = st.selectbox("Select Existing Category*", options=existing_cats + ["➕ Create New Category..."])
        new_custom_cat = st.text_input("Or type new category name (if 'Create New' selected above):")
        
        new_season = st.selectbox("Season", ["Any", "Spring", "Summer", "Autumn", "Winter"])
        new_dur = st.selectbox("Duration", ["<4hr", "<24hrs", "<48hrs", "<7days"])
        new_cost = st.selectbox("Cost", ["Free", "Low", "Medium", "High"])
        new_notes = st.text_area("Notes / Comments")
        
        submitted = st.form_submit_button("Add Activity")
        if submitted:
            final_cat = new_custom_cat.strip() if cat_choice == "➕ Create New Category..." else cat_choice
            
            if not new_act or not final_cat:
                st.error("Please provide both an Activity name and Category!")
            else:
                df = load_data()
                new_row = pd.DataFrame([{
                    "Activity": new_act,
                    "Category": final_cat,
                    "Season": new_season,
                    "Duration": new_dur,
                    "Cost": new_cost,
                    "Comments": new_notes
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success(f"Added '{new_act}' under '{final_cat}' permanently to Google Sheets!")

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
            st.success(f"Removed '{to_delete}' from Google Sheets!")
            st.rerun()
