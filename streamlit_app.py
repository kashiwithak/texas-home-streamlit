import streamlit as st
import pandas as pd

# -----------------------------
# CONFIG: criteria + weights
# -----------------------------
CRITERIA = [
  ("Environmental", "Air quality", 4),
  ("Environmental", "Distance from chemical plants / industrial areas", 5),
  ("Environmental", "Flood zone / elevation", 5),
  ("Environmental", "Water quality", 4),
  ("Environmental", "No large farmland nearby", 3),
  ("Environmental", "Radiation/EMF (no towers/power lines)", 3),
  ("Schools", "ISD zoned", 4),
  ("Schools", "Rating of zoned schools (must be 'A')", 5),
  ("Schools", "Diversity", 3),
  ("Schools", "MPC alignment", 4),
  ("Schools", "Classroom visit / feel", 2),
  ("Neighborhood", "Whole Foods / Sprouts nearby", 4),
  ("Neighborhood", "Trees / greenery", 3),
  ("Neighborhood", "Parks & trails", 4),
  ("Neighborhood", "Good food options", 3),
  ("Neighborhood", "Indian groceries nearby", 3),
  ("Neighborhood", "Low crime", 5),
  ("Neighborhood", "Gyms / YMCA / rec center nearby", 3),
  ("Neighborhood", "Tesla superchargers / service nearby", 3),
  ("Community + Home", "Property tax rate", 5),
  ("Community + Home", "HOA / MUD / PID fees + restrictions", 4),
  ("Community + Home", "Commute to downtown", 3),
  ("Community + Home", "Grass type suitability", 1),
  ("Community + Home", "Solar allowed / backup power ready", 3),
  ("Community + Home", "EV charging (NEMA 14-50)", 2),
  ("Community + Home", "Utility cost & internet options", 4),
  ("Community + Home", "Lot layout & orientation", 4),
  ("Community + Home", "Backyard size & offset from neighbors", 4),
  ("Community + Home", "Amenity crowding", 3),
  ("Community + Home", "Demographics / vibe", 2),
  ("Community + Home", "Cars / neighborhood upkeep", 3),
  ("Community + Home", "Kid amenities (playgrounds, trails, parks)", 4),
  ("Builder", "Incentives offered", 3),
  ("Builder", "Warranty coverage", 4),
  ("Builder", "Ready-to-move inventory", 2),
  ("Builder", "Energy efficiency", 4),
]

CATEGORIES = [
    "Environmental",
    "Schools",
    "Neighborhood",
    "Community + Home",
    "Builder",
]

# Page + state
st.set_page_config(page_title="Texas Home Tour Scoring", layout="wide")
if "homes" not in st.session_state:
    st.session_state.homes = []

st.title("🏡 Texas Home Tour Scoring (Streamlit)")

# --- Add Home Form ---
with st.form("add_home", clear_on_submit=True):
    st.subheader("Add a Home")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        address = st.text_input("Address / Nickname*")
    with c2:
        city = st.text_input("City")
    with c3:
        builder = st.text_input("Builder")
    with c4:
        community = st.text_input("Community")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        incentives = st.text_input("Incentives")
    with c6:
        schoolElem = st.text_input("Zoned Elementary")
    with c7:
        schoolMiddle = st.text_input("Zoned Middle")
    with c8:
        schoolHigh = st.text_input("Zoned High")

    notes = st.text_area("Notes")

    scores = {}
    for cat in CATEGORIES:
        st.markdown(f"### {cat}")
        for (c_cat, name, weight) in [c for c in CRITERIA if c[0] == cat]:
            val = st.slider(f"{name} (Weight {weight})", 1, 5, 3, key=f"add-{cat}-{name}")
            scores[f"{c_cat}::{name}"] = val

    if st.form_submit_button("Add Home"):
        if not address.strip():
            st.warning("Please enter an address/nickname.")
        else:
            st.session_state.homes.append({
                "info": {
                    "address": address,
                    "city": city,
                    "builder": builder,
                    "community": community,
                    "incentives": incentives,
                    "schoolElem": schoolElem,
                    "schoolMiddle": schoolMiddle,
                    "schoolHigh": schoolHigh,
                    "notes": notes,
                },
                "scores": scores,
            })
            st.success(f"Added {address}")

# --- Helpers ---
def categorySubtotal(scores, category):
    return sum((scores.get(f"{c_cat}::{name}", 0) * weight)
               for (c_cat, name, weight) in CRITERIA if c_cat == category)

def overallScore(scores):
    return sum((scores.get(f"{c_cat}::{name}", 0) * weight) for (c_cat, name, weight) in CRITERIA)

maxPossible = sum(5 * weight for (_, _, weight) in CRITERIA)

# --- Cards per home ---
if st.session_state.homes:
    st.subheader("Your Homes")
    for idx, h in enumerate(st.session_state.homes):
        info = h["info"]
        scores = h["scores"]
        st.markdown(f"### {info['address']} | Overall: **{overallScore(scores)} / {maxPossible}**")
        st.caption(f"{info.get('city','')} • {info['community']} • {info['builder']} • Incentives: {info['incentives']}")
        st.caption(f"Schools: {info['schoolElem']} / {info['schoolMiddle']} / {info['schoolHigh']}")
        cols = st.columns(len(CATEGORIES))
        for i, cat in enumerate(CATEGORIES):
            with cols[i]:
                st.metric(cat, categorySubtotal(scores, cat))
        if info["notes"]:
            st.info(info["notes"])
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"✏️ Edit {info['address']}", key=f"editbtn-{idx}"):
                st.session_state["edit_idx"] = idx
        with c2:
            if st.button(f"🗑️ Delete {info['address']}", key=f"delbtn-{idx}"):
                st.session_state.homes.pop(idx)
                st.rerun()

    # --- Quick Snapshot Table with Category Subtotals ---
    st.subheader("Quick Snapshot (sortable table)")
    rows = []
    for h in st.session_state.homes:
        info = h["info"]
        scores = h["scores"]
        row = {
            "Address": info["address"],
            "City": info.get("city", ""),
            "Builder": info["builder"],
            "Community": info["community"],
            "Elementary": info["schoolElem"],
            "Middle": info["schoolMiddle"],
            "High": info["schoolHigh"],
            "Environmental": categorySubtotal(scores, "Environmental"),
            "Schools": categorySubtotal(scores, "Schools"),
            "Neighborhood": categorySubtotal(scores, "Neighborhood"),
            "Community + Home": categorySubtotal(scores, "Community + Home"),
            "Builder Subtotal": categorySubtotal(scores, "Builder"),
            "Overall": overallScore(scores),
        }
        rows.append(row)
    snap_df = pd.DataFrame(rows)
    st.dataframe(snap_df, use_container_width=True)

    # --- Edit selected home (inline form) ---
    if "edit_idx" in st.session_state:
        idx = st.session_state["edit_idx"]
        if 0 <= idx < len(st.session_state.homes):
            st.markdown("---")
            st.subheader(f"Edit Home – {st.session_state.homes[idx]['info']['address']}")
            e_info = st.session_state.homes[idx]["info"].copy()
            e_scores = st.session_state.homes[idx]["scores"].copy()
            with st.form("edit_home_form"):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    e_address = st.text_input("Address / Nickname*", value=e_info["address"], key=f"edit-addr-{idx}")
                with c2:
                    e_city = st.text_input("City", value=e_info.get("city",""), key=f"edit-city-{idx}")
                with c3:
                    e_builder = st.text_input("Builder", value=e_info["builder"], key=f"edit-builder-{idx}")
                with c4:
                    e_community = st.text_input("Community", value=e_info["community"], key=f"edit-community-{idx}")
                c5, c6, c7 = st.columns(3)
                with c5:
                    e_incentives = st.text_input("Incentives", value=e_info["incentives"], key=f"edit-incent-{idx}")
                with c6:
                    e_elem = st.text_input("Zoned Elementary", value=e_info["schoolElem"], key=f"edit-elem-{idx}")
                with c7:
                    e_mid = st.text_input("Zoned Middle", value=e_info["schoolMiddle"], key=f"edit-mid-{idx}")
                e_high = st.text_input("Zoned High", value=e_info["schoolHigh"], key=f"edit-high-{idx}")
                e_notes = st.text_area("Notes", value=e_info["notes"], key=f"edit-notes-{idx}")

                st.markdown("#### Adjust Scores (1–5)")
                for cat in CATEGORIES:
                    st.markdown(f"**{cat}**")
                    for (c_cat, name, weight) in [c for c in CRITERIA if c[0] == cat]:
                        key = f"{c_cat}::{name}"
                        cur = int(e_scores.get(key, 3))
                        new_val = st.slider(f"{name} (w {weight})", 1, 5, cur, key=f"edit-{idx}-{name}")
                        e_scores[key] = new_val

                ec1, ec2 = st.columns(2)
                with ec1:
                    if st.form_submit_button("Save changes"):
                        st.session_state.homes[idx] = {
                            "info": {
                                "address": e_address,
                                "city": e_city,
                                "builder": e_builder,
                                "community": e_community,
                                "incentives": e_incentives,
                                "schoolElem": e_elem,
                                "schoolMiddle": e_mid,
                                "schoolHigh": e_high,
                                "notes": e_notes,
                            },
                            "scores": e_scores,
                        }
                        del st.session_state["edit_idx"]
                        st.success("Saved changes")
                        st.rerun()
                with ec2:
                    if st.form_submit_button("Cancel"):
                        del st.session_state["edit_idx"]
                        st.rerun()
        else:
            del st.session_state["edit_idx"]
else:
    st.info("No homes added yet. Use the form above.")
