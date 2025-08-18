
import streamlit as st
import pandas as pd
import base64

# ----------------------------------
# FINAL CATEGORIES & CRITERIA (weighted 1-5)
# ----------------------------------
CRITERIA = [
  # Environmental
  ("Environmental", "Flood zone risk / elevation", 5),
  ("Environmental", "High-voltage power lines nearby", 4),
  ("Environmental", "Industrial complexes nearby", 5),
  ("Environmental", "Noise pollution", 3),
  # Neighborhood
  ("Neighborhood", "Whole Foods proximity", 4),
  ("Neighborhood", "Indian grocery proximity", 4),
  ("Neighborhood", "Amenity proximity (gym/YMCA/rec)", 3),
  ("Neighborhood", "Greenery / trees", 3),
  # Community
  ("Community", "Amenities quality", 4),
  ("Community", "Completion stage (build-out)", 3),
  ("Community", "Trees / parks / playgrounds", 4),
  ("Community", "Demographics fit", 2),
  # Home
  ("Home", "Lot shape", 3),
  ("Home", "Backyard size", 4),
  ("Home", "Location within community", 4),
  ("Home", "Grass quality", 2),
  # Builder
  ("Builder", "Quality of construction", 5),
  ("Builder", "Incentives", 3),
  ("Builder", "Warranty", 4),
  ("Builder", "Energy efficiency", 4),
  # School
  ("School", "Zoned school ratings", 5),
]

CATEGORIES = ["Environmental","Neighborhood","Community","Home","Builder","School"]

# ------------------
# Page + state
# ------------------
st.set_page_config(page_title="Texas Home Tour Scoring", layout="centered")
if "homes" not in st.session_state:
    st.session_state.homes = []

st.title("🏡 Texas Home Tour Scoring (Streamlit)")

# Mobile tweaks
st.markdown(
    """
    <style>
      .block-container { padding-top: 0.8rem; padding-bottom: 2.5rem; }
      .stButton>button { padding: 0.55rem 0.9rem; border-radius: 10px; }
      label[data-baseweb='typography'] { font-size: 0.95rem; }
      .notes-cell { white-space: normal !important; }
      img { border-radius: 8px; }
    </style>
    """
    ,
    unsafe_allow_html=True,
)

# ------------------
# Add Home Form
# ------------------
with st.form("add_home", clear_on_submit=True):
    st.subheader("Add a Home")

    c1, c2, c3 = st.columns(3)
    with c1:
        address = st.text_input("Address / Nickname*")
        city = st.text_input("City")
        mpc = st.text_input("Master Plan Community (MPC)")
    with c2:
        builder = st.text_input("Builder")
        tax_rate = st.text_input("Property tax rate (e.g., 2.3%)")
        yearly_hoa = st.number_input("Yearly HOA ($)", min_value=0, step=50, value=0)
    with c3:
        mud = st.text_input("MUD (yes/no or rate)")
        pid = st.text_input("PID (yes/no or rate)")
        restrictions = st.text_input("Restrictions (brief)")

    c4, c5, c6 = st.columns(3)
    with c4:
        isp = st.text_input("ISP provider (primary)")
        hoa_includes = st.multiselect(
            "HOA includes",
            ["Water","Sewer","Garbage","Gas","Electric","Internet"]
        )
    with c5:
        school_elem = st.text_input("Zoned Elementary")
        school_mid = st.text_input("Zoned Middle")
    with c6:
        incentives = st.text_input("Incentives (builder/community)")
        notes = st.text_area("Notes")

    # Photos
    photo_urls_raw = st.text_input("Photo URLs (comma-separated)", placeholder="https://photos.app..., https://drive.google.com/...")
    uploads = st.file_uploader("Upload photos (optional)", type=["png","jpg","jpeg","webp"], accept_multiple_files=True)

    st.markdown("### Score this home")
    scores = {}
    for cat in CATEGORIES:
        st.markdown(f"**{cat}**")
        for (c_cat, name, weight) in [c for c in CRITERIA if c[0]==cat]:
            val = st.slider(f"{name} (w{weight})", 1, 5, 3, key=f"add-{cat}-{name}")
            scores[f"{c_cat}::{name}"] = val

    submitted = st.form_submit_button("Add Home")
    if submitted:
        if not address.strip():
            st.warning("Please enter an address/nickname.")
        else:
            url_list = [u.strip() for u in (photo_urls_raw or "").split(",") if u.strip()]
            photo_blobs = []
            for f in uploads or []:
                try:
                    photo_blobs.append({"name": f.name, "type": f.type, "bytes": f.getbuffer().tobytes()})
                except Exception:
                    pass
            st.session_state.homes.append({
                "info": {
                    "address": address, "city": city, "mpc": mpc, "builder": builder,
                    "tax_rate": tax_rate, "yearly_hoa": yearly_hoa, "mud": mud, "pid": pid,
                    "restrictions": restrictions, "hoa_includes": hoa_includes, "isp": isp,
                    "school_elem": school_elem, "school_mid": school_mid,
                    "incentives": incentives, "notes": notes, "photo_urls": url_list
                },
                "photos": photo_blobs,
                "scores": scores,
            })
            st.success(f"Added {address}")

# ------------------
# Helpers
# ------------------
def categorySubtotal(scores, category):
    return sum((scores.get(f"{c_cat}::{name}", 0) * weight) for (c_cat, name, weight) in CRITERIA if c_cat == category)

def overallScore(scores):
    return sum((scores.get(f"{c_cat}::{name}", 0) * weight) for (c_cat, name, weight) in CRITERIA)

# ------------------
# Summary table (mobile + desktop)
# ------------------
if st.session_state.homes:
    st.subheader("Quick Summary")
    mode_mobile = st.toggle("📱 Compact (mobile) view", value=True)

    if mode_mobile:
        # Compact set of columns
        header = st.columns([2,3,2,2,3,1.2,1.2])
        header[0].markdown("**City**")
        header[1].markdown("**MPC**")
        header[2].markdown("**Tax**")
        header[3].markdown("**Overall**")
        header[4].markdown("**Notes**")
        header[5].markdown("**Photo**")
        header[6].markdown("**⋯**")

        for idx, h in enumerate(st.session_state.homes):
            info, scores = h["info"], h["scores"]
            overall = overallScore(scores)
            note_txt = (info.get("notes","") or "").strip()
            if len(note_txt) > 60: note_txt = note_txt[:57] + "…"
            row = st.columns([2,3,2,2,3,1.2,1.2])
            row[0].write(info.get("city",""))
            row[1].write(info.get("mpc",""))
            row[2].write(info.get("tax_rate",""))
            row[3].write(overall)
            row[4].write(note_txt)
            urls = info.get("photo_urls", [])
            if urls:
                row[5].markdown(f"[View]({urls[0]})")
            elif h.get("photos"):
                imgdata = h["photos"][0]["bytes"]
                b64 = base64.b64encode(imgdata).decode("utf-8")
                row[5].markdown(f'![](data:image/png;base64,{b64})')
            else:
                row[5].write("-")
            a1, a2 = row[6].columns(2)
            if a1.button("✏️", key=f"m-edit-{idx}"):
                st.session_state["edit_idx"] = idx
            if a2.button("🗑️", key=f"m-del-{idx}"):
                st.session_state.homes.pop(idx)
                st.rerun()

        with st.expander("Show details (neighborhood, HOA, schools, ISP, etc.)"):
            # Detailed info rows
            for h in st.session_state.homes:
                info, scores = h["info"], h["scores"]
                st.markdown(f"**{info.get('address','(no name)')}** — {info.get('city','')} • {info.get('mpc','')} • {info.get('builder','')}")
                st.caption(f"Tax {info.get('tax_rate','')} • HOA ${info.get('yearly_hoa',0)} • MUD {info.get('mud','')} • PID {info.get('pid','')} • ISP {info.get('isp','')}")
                st.caption(f"Elem: {info.get('school_elem','')} • Mid: {info.get('school_mid','')} • HOA includes: {', '.join(info.get('hoa_includes',[])) or '-'} • Restrictions: {info.get('restrictions','-')}")
                subs = [f"{cat}: {categorySubtotal(scores, cat)}" for cat in CATEGORIES]
                st.write(" / ".join(subs))
                st.divider()
    else:
        # Full desktop with all requested columns
        header = st.columns([1.6,2,2,1.4,1.4,1.4,1.2,1.2,2.2,2.2,2.2,1.6,2.0,1.2,1.2])
        cols_titles = ["City","MPC","Builder","Tax","HOA$/yr","MUD","PID","ISP","Elem","Middle","Restrictions","Includes","Overall","Photo","⋯"]
        for c, t in zip(header, cols_titles):
            c.markdown(f"**{t}**")

        for idx, h in enumerate(st.session_state.homes):
            info, scores = h["info"], h["scores"]
            row = st.columns([1.6,2,2,1.4,1.4,1.4,1.2,1.2,2.2,2.2,2.2,1.6,2.0,1.2,1.2])
            row[0].write(info.get("city",""))
            row[1].write(info.get("mpc",""))
            row[2].write(info.get("builder",""))
            row[3].write(info.get("tax_rate",""))
            row[4].write(info.get("yearly_hoa",0))
            row[5].write(info.get("mud",""))
            row[6].write(info.get("pid",""))
            row[7].write(info.get("isp",""))
            row[8].write(info.get("school_elem",""))
            row[9].write(info.get("school_mid",""))
            row[10].write(info.get("restrictions",""))
            row[11].write(", ".join(info.get("hoa_includes",[])) or "-")
            row[12].write(overallScore(scores))
            urls = info.get("photo_urls", [])
            if urls:
                row[13].markdown(f"[View]({urls[0]})")
            elif h.get("photos"):
                imgdata = h["photos"][0]["bytes"]
                b64 = base64.b64encode(imgdata).decode("utf-8")
                row[13].markdown(f'![](data:image/png;base64,{b64})')
            else:
                row[13].write("-")
            a1, a2 = row[14].columns(2)
            if a1.button("✏️", key=f"d-edit-{idx}"):
                st.session_state["edit_idx"] = idx
            if a2.button("🗑️", key=f"d-del-{idx}"):
                st.session_state.homes.pop(idx)
                st.rerun()
else:
    st.info("No homes added yet. Use the form above.")
