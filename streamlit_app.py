
import streamlit as st
import pandas as pd
import base64

# -----------------------------
# CONFIG: final categories + weights (incl. Vaastu)
# -----------------------------
CRITERIA = [
  # Environmental
  ("Environmental", "Flood zone", 5),
  ("Environmental", "High voltage power lines", 4),
  ("Environmental", "Industrial complex proximity", 5),
  ("Environmental", "Noise pollution", 3),
  # Neighborhood
  ("Neighborhood", "Whole Foods proximity", 4),
  ("Neighborhood", "Indian Grocery proximity", 4),
  ("Neighborhood", "Amenity proximity (gyms/rec/Tesla)", 3),
  ("Neighborhood", "Greenery", 3),
  # Community
  ("Community", "Amenities quality", 4),
  ("Community", "Completion stage", 3),
  ("Community", "Trees & parks", 3),
  ("Community", "Playgrounds", 3),
  ("Community", "Demographics", 2),
  # Home
  ("Home", "Lot shape", 3),
  ("Home", "Backyard size", 4),
  ("Home", "Location within community", 3),
  ("Home", "Grass quality", 1),
  # Builder
  ("Builder", "Quality of construction", 5),
  ("Builder", "Incentives", 3),
  ("Builder", "Warranty", 4),
  ("Builder", "Energy efficiency", 4),
  # School
  ("School", "Zoned school ratings", 5),
  # Vaastu (pass/fail -> 5 or 0 then * weight)
  ("Vaastu", "Main Entrance (East/North ✅, South ❌)", 5),
  ("Vaastu", "Kitchen (SE/NW ✅, NE ❌)", 4),
  ("Vaastu", "Master Bedroom (SW ✅, NE ❌)", 4),
  ("Vaastu", "Pooja Room (NE/E ✅, South/under stairs ❌)", 3),
]

CATEGORIES = ["Environmental","Neighborhood","Community","Home","Builder","School","Vaastu"]

# -----------------------------
# PAGE CONFIG + MOBILE TWEAKS
# -----------------------------
st.set_page_config(page_title="Texas Home Tour Scoring", layout="centered")
st.title("🏡 Texas Home Tour Scoring (Streamlit)")

st.markdown(
    """
    <style>
      .block-container { padding-top: 1rem; padding-bottom: 3rem; }
      .stButton>button { padding: 0.6rem 0.9rem; border-radius: 10px; }
      label[data-baseweb="typography"] { font-size: 0.95rem; }
      div[data-testid="stVerticalBlock"] p { margin-bottom: 0.25rem; }
      img.thumb { max-height: 64px; border-radius: 6px; }
      .notes-cell { white-space: normal; line-height: 1.2; }
      .table-row { border-bottom: 1px solid #eee; padding: .2rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "homes" not in st.session_state:
    st.session_state.homes = []
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None

# -----------------------------
# HELPERS
# -----------------------------
def criterion_key(cat, name):
    return f"{cat}::{name}"

def category_subtotal(scores, category):
    total = 0
    for (c_cat, name, weight) in CRITERIA:
        if c_cat != category: 
            continue
        val = scores.get(criterion_key(c_cat,name), 0)
        total += val * weight
    return total

def vaastu_pass_count(scores):
    return sum(1 for (c_cat, name, _) in CRITERIA if c_cat=="Vaastu" and scores.get(criterion_key(c_cat,name),0) >= 5)

def overall_score(scores):
    return sum(scores.get(criterion_key(c_cat,name),0) * weight for (c_cat,name,weight) in CRITERIA)

def homes_dataframe(homes):
    rows = []
    for h in homes:
        info, scores = h["info"], h["scores"]
        rows.append({
            "City": info.get("city",""),
            "MPC": info.get("community",""),
            "Builder": info.get("builder",""),
            "Environmental": category_subtotal(scores, "Environmental"),
            "Neighborhood": category_subtotal(scores, "Neighborhood"),
            "Community": category_subtotal(scores, "Community"),
            "Home": category_subtotal(scores, "Home"),
            "School": category_subtotal(scores, "School"),
            "Builder Subtotal": category_subtotal(scores, "Builder"),
            "Vaastu": f"{vaastu_pass_count(scores)}/4",
            "Overall": overall_score(scores),
            "Notes": info.get("notes",""),
            "Photo": (info.get("photo_urls") or [""])[0],
            # Cost & policy
            "PropertyTax": info.get("property_tax",""),
            "MUD": info.get("mud",""),
            "PID": info.get("pid",""),
            "YearlyHOA": info.get("hoa",""),
            "Restrictions": info.get("restrictions",""),
            # HOA includes
            "HOA_Water": info.get("hoa_includes",{}).get("Water", False),
            "HOA_Sewer": info.get("hoa_includes",{}).get("Sewer", False),
            "HOA_Garbage": info.get("hoa_includes",{}).get("Garbage", False),
            "HOA_Gas": info.get("hoa_includes",{}).get("Gas", False),
            "HOA_Electric": info.get("hoa_includes",{}).get("Electric", False),
            "HOA_Internet": info.get("hoa_includes",{}).get("Internet", False),
            "ISP": info.get("isp",""),
            # Schools
            "ZonedElem": info.get("schoolElem",""),
            "ZonedMid": info.get("schoolMiddle",""),
            "ZonedHigh": info.get("schoolHigh",""),
            # Ref
            "Address/Nickname": info.get("address",""),
        })
    return pd.DataFrame(rows)

# -----------------------------
# ADD / EDIT FORM
# -----------------------------
def add_or_edit_form(edit_idx=None):
    is_edit = edit_idx is not None
    st.subheader("Edit Home" if is_edit else "Add a Home")

    info = {}
    prev_scores = {}
    if is_edit:
        info = st.session_state.homes[edit_idx]["info"].copy()
        prev_scores = st.session_state.homes[edit_idx]["scores"].copy()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        city = st.text_input("City", value=info.get("city",""))
    with c2:
        community = st.text_input("MPC / Community", value=info.get("community",""))
    with c3:
        builder = st.text_input("Builder", value=info.get("builder",""))
    with c4:
        address = st.text_input("Address/Nickname", value=info.get("address",""))

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        tax = st.text_input("Property Tax Rate", value=info.get("property_tax",""))
    with c6:
        mud = st.text_input("MUD", value=info.get("mud",""))
    with c7:
        pid = st.text_input("PID", value=info.get("pid",""))
    with c8:
        hoa = st.text_input("Yearly HOA ($)", value=info.get("hoa",""))

    restrictions = st.text_area("Restrictions", value=info.get("restrictions",""))
    st.markdown("**HOA Includes:**")
    hoa_cols = st.columns(6)
    includes = {}
    for i, field in enumerate(["Water","Sewer","Garbage","Gas","Electric","Internet"]):
        includes[field] = hoa_cols[i].checkbox(field, value=info.get("hoa_includes",{}).get(field, False))

    isp = st.text_input("ISP Provider", value=info.get("isp",""))
    schoolElem = st.text_input("Zoned Elementary", value=info.get("schoolElem",""))
    schoolMiddle = st.text_input("Zoned Middle", value=info.get("schoolMiddle",""))
    schoolHigh = st.text_input("Zoned High (optional)", value=info.get("schoolHigh",""))
    notes = st.text_area("Notes", value=info.get("notes",""))

    photo_urls_raw = st.text_input("Photo URLs (comma-separated)", value=",".join(info.get("photo_urls",[])))
    uploads = st.file_uploader("Upload photos", type=["png","jpg","jpeg","webp"], accept_multiple_files=True)

    scores = {}
    for cat in CATEGORIES:
        st.markdown(f"### {cat}")
        for (c_cat, name, weight) in [c for c in CRITERIA if c[0] == cat]:
            key = criterion_key(c_cat,name)
            if c_cat == "Vaastu":
                default = bool(prev_scores.get(key, 0) >= 5) if is_edit else False
                val = st.checkbox(name, value=default, key=f"{('e' if is_edit else 'a')}-{cat}-{name}")
                scores[key] = 5 if val else 0
            else:
                default = int(prev_scores.get(key, 3)) if is_edit else 3
                val = st.slider(f"{name} (Weight {weight})", 1, 5, default, key=f"{('e' if is_edit else 'a')}-{cat}-{name}")
                scores[key] = val

    if is_edit:
        c1, c2 = st.columns(2)
        if c1.button("Save changes"):
            # Convert uploads to in-memory bytes
            photo_blobs = st.session_state.homes[edit_idx].get("photos", [])
            if uploads:
                photo_blobs = [{"name": f.name, "type": f.type, "bytes": f.getbuffer().tobytes()} for f in uploads]
            st.session_state.homes[edit_idx] = {
                "info": {
                    "city": city, "community": community, "builder": builder, "address": address,
                    "property_tax": tax, "mud": mud, "pid": pid, "hoa": hoa,
                    "restrictions": restrictions, "hoa_includes": includes, "isp": isp,
                    "schoolElem": schoolElem, "schoolMiddle": schoolMiddle, "schoolHigh": schoolHigh,
                    "notes": notes, "photo_urls": [u.strip() for u in photo_urls_raw.split(",") if u.strip()],
                },
                "photos": photo_blobs,
                "scores": scores,
            }
            st.session_state.edit_idx = None
            st.success("Saved changes")
            st.rerun()
        if c2.button("Cancel"):
            st.session_state.edit_idx = None
            st.rerun()
    else:
        if st.form_submit_button("Add Home"):
            photo_blobs = []
            if uploads:
                photo_blobs = [{"name": f.name, "type": f.type, "bytes": f.getbuffer().tobytes()} for f in uploads]
            st.session_state.homes.append({
                "info": {
                    "city": city, "community": community, "builder": builder, "address": address,
                    "property_tax": tax, "mud": mud, "pid": pid, "hoa": hoa,
                    "restrictions": restrictions, "hoa_includes": includes, "isp": isp,
                    "schoolElem": schoolElem, "schoolMiddle": schoolMiddle, "schoolHigh": schoolHigh,
                    "notes": notes, "photo_urls": [u.strip() for u in photo_urls_raw.split(",") if u.strip()],
                },
                "photos": photo_blobs,
                "scores": scores,
            })
            st.success(f"Added {address}")

# -----------------------------
# RENDER: Add or Edit
# -----------------------------
if st.session_state.edit_idx is not None:
    add_or_edit_form(st.session_state.edit_idx)
else:
    # Use a container form for add; no experimental_rerun used anywhere
    with st.form("add_form_container", clear_on_submit=False):
        add_or_edit_form(None)

st.markdown("---")

# -----------------------------
# SUMMARY TABLES
# -----------------------------
mode_mobile = st.toggle("📱 Mobile-friendly summary (compact)", value=True)

def make_thumb_cell(info, photos_obj):
    urls = info.get("photo_urls") or []
    if urls:
        return f"[View]({urls[0]})"
    if photos_obj:
        b = photos_obj[0]["bytes"]
        b64 = base64.b64encode(b).decode("utf-8")
        return f'![](data:image/png;base64,{b64})'
    return "—"

if st.session_state.homes:
    st.subheader("Quick Summary")

    if mode_mobile:
        # Compact view
        header_cols = st.columns([2.2,3,2,2.2,3,1.2,1.2])
        header_cols[0].markdown("**City**")
        header_cols[1].markdown("**MPC**")
        header_cols[2].markdown("**Overall**")
        header_cols[3].markdown("**Vaastu**")
        header_cols[4].markdown("**Notes**")
        header_cols[5].markdown("**Photo**")
        header_cols[6].markdown("**⋯**")

        for ridx, h in enumerate(st.session_state.homes):
            info, scores = h["info"], h["scores"]
            overall = overall_score(scores)
            vcount = vaastu_pass_count(scores)
            note_txt = (info.get("notes","") or "").strip()
            if len(note_txt) > 60: note_txt = note_txt[:57] + "…"
            row_cols = st.columns([2.2,3,2,2.2,3,1.2,1.2])
            row_cols[0].write(info.get("city",""))
            row_cols[1].write(info.get("community",""))
            row_cols[2].write(overall)
            row_cols[3].write(f"{vcount}/4")
            row_cols[4].write(note_txt)
            row_cols[5].markdown(make_thumb_cell(info, h.get("photos", [])))
            e1, e2 = row_cols[6].columns(2)
            if e1.button("✏️", key=f"m-edit-{ridx}"):
                st.session_state.edit_idx = ridx
                st.rerun()
            if e2.button("🗑️", key=f"m-del-{ridx}"):
                st.session_state.homes.pop(ridx)
                st.rerun()

        with st.expander("Show category subtotals"):
            header_cols = st.columns([2,2,2,2,2,2,2,2,3])
            header_cols[0].markdown("**City**")
            header_cols[1].markdown("**MPC**")
            header_cols[2].markdown("**Builder**")
            header_cols[3].markdown("**Environmental**")
            header_cols[4].markdown("**Neighborhood**")
            header_cols[5].markdown("**Community**")
            header_cols[6].markdown("**Home**")
            header_cols[7].markdown("**School**")
            header_cols[8].markdown("**Overall**")
            for h in st.session_state.homes:
                info, scores = h["info"], h["scores"]
                row = st.columns([2,2,2,2,2,2,2,2,3])
                row[0].write(info.get("city",""))
                row[1].write(info.get("community",""))
                row[2].write(info.get("builder",""))
                row[3].write(category_subtotal(scores,"Environmental"))
                row[4].write(category_subtotal(scores,"Neighborhood"))
                row[5].write(category_subtotal(scores,"Community"))
                row[6].write(category_subtotal(scores,"Home"))
                row[7].write(category_subtotal(scores,"School"))
                row[8].write(overall_score(scores))

    else:
        # Desktop/full view
        header_cols = st.columns([2,2,2,2,2,2,2,2,2,2.2,3,1,1])
        header_cols[0].markdown("**City**")
        header_cols[1].markdown("**MPC**")
        header_cols[2].markdown("**Builder**")
        header_cols[3].markdown("**Environmental**")
        header_cols[4].markdown("**Neighborhood**")
        header_cols[5].markdown("**Community**")
        header_cols[6].markdown("**Home**")
        header_cols[7].markdown("**School**")
        header_cols[8].markdown("**Builder Subtotal**")
        header_cols[9].markdown("**Vaastu**")
        header_cols[10].markdown("**Notes**")
        header_cols[11].markdown("**Photo**")
        header_cols[12].markdown("**⋯**")

        for ridx, h in enumerate(st.session_state.homes):
            info, scores = h["info"], h["scores"]
            row_cols = st.columns([2,2,2,2,2,2,2,2,2,2.2,3,1,1])
            row_cols[0].write(info.get("city",""))
            row_cols[1].write(info.get("community",""))
            row_cols[2].write(info.get("builder",""))
            row_cols[3].write(category_subtotal(scores,"Environmental"))
            row_cols[4].write(category_subtotal(scores,"Neighborhood"))
            row_cols[5].write(category_subtotal(scores,"Community"))
            row_cols[6].write(category_subtotal(scores,"Home"))
            row_cols[7].write(category_subtotal(scores,"School"))
            row_cols[8].write(category_subtotal(scores,"Builder"))
            row_cols[9].write(f"{vaastu_pass_count(scores)}/4")
            row_cols[10].write(info.get("notes",""))
            # Photo cell
            urls = info.get("photo_urls") or []
            if urls:
                row_cols[11].markdown(f"[View]({urls[0]})")
            elif h.get("photos"):
                b = h["photos"][0]["bytes"]
                b64 = base64.b64encode(b).decode("utf-8")
                row_cols[11].markdown(f'![](data:image/png;base64,{b64})')
            else:
                row_cols[11].write("—")
            # Actions
            e1, e2 = row_cols[12].columns(2)
            if e1.button("✏️", key=f"d-edit-{ridx}"):
                st.session_state.edit_idx = ridx
                st.rerun()
            if e2.button("🗑️", key=f"d-del-{ridx}"):
                st.session_state.homes.pop(ridx)
                st.rerun()

    st.markdown("---")
    # ===== CSV Export Buttons =====
    df = homes_dataframe(st.session_state.homes)
    csv_all = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Full Summary CSV", data=csv_all, file_name="home_summary.csv", mime="text/csv")

# -----------------------------
# VAASTU QUICK REFERENCE
# -----------------------------
st.markdown("### 🧭 Vaastu Quick Reference")
st.markdown("""
**Primary (deal breakers):**
- **Main Entrance:** Stand inside facing out. ✅ East/North, ⚠️ West OK, ❌ South avoid.
- **Kitchen:** ✅ Southeast/Northwest; ❌ Northeast.
- **Master Bedroom:** ✅ Southwest; ❌ Northeast.
- **Pooja/Prayer Space:** ✅ Northeast/East; ❌ South/under stairs/near bathrooms.

**Secondary (good to have):**
- Staircase: South/West preferred.
- Toilets: West/Northwest best; avoid Northeast.
- Windows: More on North/East sides.
- Water storage: Northeast preferred.
- Site slope: South → North preferred.
""")
