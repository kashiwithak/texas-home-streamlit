import streamlit as st
import pandas as pd

st.set_page_config(page_title="Texas Home Tour Scoring", layout="wide")

# Initialize session state
if "homes" not in st.session_state:
    st.session_state.homes = []
if "view_idx" not in st.session_state:
    st.session_state.view_idx = None
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None

# Dummy scoring function for now
def calc_score(home):
    return sum(val for val in home.get("scores", {}).values())

# --- Tabs ---
tab_input, tab_props = st.tabs(["➕ Input", "🏘️ Properties"])

with tab_input:
    st.header("Add / Edit Home")
    with st.form("add_home", clear_on_submit=True):
        address = st.text_input("Address / Nickname*")
        city = st.text_input("City")
        builder = st.text_input("Builder")
        community = st.text_input("Community")
        notes = st.text_area("Notes")
        photo_url = st.text_input("Main Photo URL")
        submitted = st.form_submit_button("Save")
        if submitted:
            if not address.strip():
                st.warning("Address required")
            else:
                home = {
                    "address": address,
                    "city": city,
                    "builder": builder,
                    "community": community,
                    "notes": notes,
                    "photo": photo_url,
                    "scores": {"dummy": 5}, # placeholder
                }
                if st.session_state.edit_idx is not None:
                    st.session_state.homes[st.session_state.edit_idx] = home
                    st.session_state.edit_idx = None
                else:
                    st.session_state.homes.append(home)
                st.success(f"Saved {address}")

with tab_props:
    st.header("Properties")
    if st.session_state.view_idx is not None:
        home = st.session_state.homes[st.session_state.view_idx]
        st.subheader(home["address"])
        st.image(home["photo"], width=400)
        st.write(home)
        if st.button("⬅ Back"):
            st.session_state.view_idx = None
            st.experimental_rerun()
    else:
        if not st.session_state.homes:
            st.info("No homes yet")
        else:
            cols_per_row = 4
            for i, home in enumerate(st.session_state.homes):
                if i % cols_per_row == 0:
                    cols = st.columns(cols_per_row)
                with cols[i % cols_per_row]:
                    score = calc_score(home)
                    card_html = f"""
                    <div style='position:relative; cursor:pointer; border:1px solid #ddd; border-radius:10px; overflow:hidden; margin:5px'>
                        <img src='{home.get("photo","")}' style='width:100%; height:200px; object-fit:cover;'>
                        <div style='position:absolute; top:5px; left:5px; background:#fff; padding:2px 6px; border-radius:5px; font-size:12px;'>Score: {score}</div>
                        <div style='position:absolute; top:5px; right:35px; background:#007bff; color:#fff; padding:2px 6px; border-radius:5px; font-size:12px;'>✏️</div>
                        <div style='position:absolute; top:5px; right:5px; background:#dc3545; color:#fff; padding:2px 6px; border-radius:5px; font-size:12px;'>🗑️</div>
                        <div style='padding:5px'>
                            <b>{home["city"]}</b><br>{home["community"]} - {home["builder"]}
                        </div>
                    </div>
                    """
                    if st.button(f"view_{i}"):
                        st.session_state.view_idx = i
                        st.experimental_rerun()
                    st.markdown(card_html, unsafe_allow_html=True)
