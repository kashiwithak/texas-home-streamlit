import streamlit as st
import pandas as pd
import base64

# -----------------------------
# CONFIG: simplified criteria + weights
# -----------------------------
CRITERIA = [
  ("Environmental", "Flood / Elevation / Air Quality", 5),
  ("Environmental", "Industrial / Power lines nearby", 4),
  ("Schools", "School Ratings", 5),
  ("Schools", "Diversity & Reputation", 3),
  ("Neighborhood", "Safety & Crime", 5),
  ("Neighborhood", "Groceries (Whole Foods / Indian)", 4),
  ("Neighborhood", "Parks & Trees", 3),
  ("Community + Home", "Property taxes & HOA/MUD", 5),
  ("Community + Home", "Commute & Utilities", 4),
  ("Community + Home", "Lot / Backyard", 4),
  ("Builder", "Builder Quality & Warranty", 4),
  ("Builder", "Incentives / Energy Efficiency", 3),
]

CATEGORIES = [
    "Environmental",
    "Schools",
    "Neighborhood",
    "Community + Home",
    "Builder",
]

# Page + session state
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

    # Photos: external links + uploads
    photo_urls_raw = st.text_input("Photo URLs (comma-separated)", placeholder="https://photos.app..., https://drive.google.com/...")
    uploads = st.file_uploader("Upload photos (optional)", type=["png","jpg","jpeg","webp"], accept_multiple_files=True)

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
            url_list = [u.strip() for u in photo_urls_raw.split(",") if u.strip()] if photo_urls_raw else []
            photo_blobs = []
            for f in uploads or []:
                try:
                    photo_blobs.append({"name": f.name, "type": f.type, "bytes": f.getbuffer().tobytes()})
                except Exception:
                    pass
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
                    "photo_urls": url_list,
                },
                "photos": photo_blobs,
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

# --- Quick Summary Table ---
if st.session_state.homes:
    st.subheader("Quick Summary")
    header_cols = st.columns([2,2,2,2,2,2,2,2,2,3,3,1,1])
    header_cols[0].markdown("**City**")
    header_cols[1].markdown("**Community**")
    header_cols[2].markdown("**Builder**")
    header_cols[3].markdown("**Environmental**")
    header_cols[4].markdown("**Schools**")
    header_cols[5].markdown("**Neighborhood**")
    header_cols[6].markdown("**Community + Home**")
    header_cols[7].markdown("**Builder**")
    header_cols[8].markdown("**Overall**")
    header_cols[9].markdown("**Notes**")
    header_cols[10].markdown("**Photo**")
    header_cols[11].markdown("**✏️**")
    header_cols[12].markdown("**🗑️**")

    for ridx, h in enumerate(st.session_state.homes):
        info = h["info"]
        scores = h["scores"]
        row_cols = st.columns([2,2,2,2,2,2,2,2,2,3,3,1,1])
        row_cols[0].write(info.get("city", ""))
        row_cols[1].write(info.get("community", ""))
        row_cols[2].write(info.get("builder", ""))
        row_cols[3].write(categorySubtotal(scores, "Environmental"))
        row_cols[4].write(categorySubtotal(scores, "Schools"))
        row_cols[5].write(categorySubtotal(scores, "Neighborhood"))
        row_cols[6].write(categorySubtotal(scores, "Community + Home"))
        row_cols[7].write(categorySubtotal(scores, "Builder"))
        row_cols[8].write(overallScore(scores))
        row_cols[9].write(info.get("notes",""))
        
        # Photo preview (URL thumbnail or first uploaded image)
        urls = info.get("photo_urls", [])
        if urls:
            row_cols[10].markdown(f"[View]({urls[0]})")
        elif h.get("photos"):
            imgdata = h["photos"][0]["bytes"]
            b64 = base64.b64encode(imgdata).decode("utf-8")
            row_cols[10].markdown(f'![](data:image/png;base64,{b64})')
        else:
            row_cols[10].write("-")

        if row_cols[11].button("✏️", key=f"table-edit-{ridx}"):
            st.session_state["edit_idx"] = ridx
        if row_cols[12].button("🗑️", key=f"table-del-{ridx}"):
            st.session_state.homes.pop(ridx)
            st.rerun()
else:
    st.info("No homes added yet. Use the form above.")
