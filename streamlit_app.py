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

CATEGORIES = sorted(set(c[0] for c in CRITERIA))

# Initialize session state
if "homes" not in st.session_state:
    st.session_state.homes = []

st.title("🏡 Texas Home Tour Scoring (Streamlit)")

# --- Form for entering home info ---
with st.form("add_home", clear_on_submit=True):
    st.subheader("Add a Home")
    address = st.text_input("Address / Nickname*")
    builder = st.text_input("Builder")
    community = st.text_input("Community")
    incentives = st.text_input("Incentives")
    schoolElem = st.text_input("Zoned Elementary")
    schoolMiddle = st.text_input("Zoned Middle")
    schoolHigh = st.text_input("Zoned High")
    notes = st.text_area("Notes")

    scores = {}
    for cat in CATEGORIES:
        st.markdown(f"### {cat}")
        for (c_cat, name, weight) in [c for c in CRITERIA if c[0]==cat]:
            val = st.slider(f"{name} (Weight {weight})", 1, 5, 3, key=f"{address}-{name}")
            scores[f"{c_cat}::{name}"] = val

    submitted = st.form_submit_button("Add Home")
    if submitted:
        if not address.strip():
            st.warning("Please enter an address/nickname.")
        else:
            st.session_state.homes.append({
                "info": {
                    "address": address, "builder": builder, "community": community,
                    "incentives": incentives, "schoolElem": schoolElem,
                    "schoolMiddle": schoolMiddle, "schoolHigh": schoolHigh,
                    "notes": notes,
                },
                "scores": scores,
            })

# --- Helper functions ---
def categorySubtotal(scores, category):
    subtotal = 0
    for (c_cat, name, weight) in CRITERIA:
        if c_cat == category:
            subtotal += scores.get(f"{c_cat}::{name}", 0) * weight
    return subtotal

def overallScore(scores):
    return sum((scores.get(f"{c_cat}::{name}", 0) * weight) for (c_cat, name, weight) in CRITERIA)

maxPossible = sum(5*weight for (_,_,weight) in CRITERIA)

# --- Display homes ---
if st.session_state.homes:
    st.subheader("Your Homes")
    for idx, h in enumerate(st.session_state.homes):
        info = h["info"]
        scores = h["scores"]
        st.markdown(f"### {info['address']} | Overall: **{overallScore(scores)} / {maxPossible}**")
        st.caption(f"{info['community']} • {info['builder']} • Incentives: {info['incentives']}")
        st.caption(f"Schools: {info['schoolElem']} / {info['schoolMiddle']} / {info['schoolHigh']}")
        # Category subtotals
        cols = st.columns(len(CATEGORIES))
        for i, cat in enumerate(CATEGORIES):
            with cols[i]:
                st.metric(cat, categorySubtotal(scores, cat))
        if info["notes"]:
            st.info(info["notes"])
        if st.button(f"Delete {info['address']}", key=f"del-{idx}"):
            st.session_state.homes.pop(idx)
            st.experimental_rerun()

    # Export CSV
    if st.button("📥 Export CSV"):
        rows = []
        for h in st.session_state.homes:
            info = h["info"]
            scores = h["scores"]
            row = {
                "Address": info["address"],
                "Builder": info["builder"],
                "Community": info["community"],
                "Incentives": info["incentives"],
                "Elementary": info["schoolElem"],
                "Middle": info["schoolMiddle"],
                "High": info["schoolHigh"],
                "Overall": overallScore(scores)
            }
            for (c_cat, name, weight) in CRITERIA:
                row[f"{c_cat} – {name} (w:{weight})"] = scores.get(f"{c_cat}::{name}", 0)
            rows.append(row)
        df = pd.DataFrame(rows)
        st.download_button("Download CSV", df.to_csv(index=False), file_name="texas_home_scores.csv", mime="text/csv")
else:
    st.info("No homes added yet. Use the form above.")
