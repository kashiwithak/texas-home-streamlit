
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
# PAGE CONFIG + STYLES
# -----------------------------
st.set_page_config(page_title="Texas Home Tour Scoring", layout="wide")
st.title("🏡 Texas Home Tour Scoring")

st.markdown(
    """
    <style>
      .block-container { padding-top: .8rem; padding-bottom: 2rem; }
      .stButton>button, .stDownloadButton>button { padding: 0.5rem 0.9rem; border-radius: 10px; }
      /* Card grid */
      .card { position: relative; overflow: hidden; border-radius: 14px; border: 1px solid #e6e6e6; }
      .thumb { width: 100%; height: 220px; object-fit: cover; display: block; }
      @media (max-width: 768px) { .thumb { height: 160px; } }
      .badge-score { position: absolute; left: 10px; top: 10px; background: rgba(0,0,0,.8); color: #fff; padding: 6px 10px; border-radius: 999px; font-size: 0.85rem; }
      .card-title { font-weight: 600; margin-top: .35rem; }
      .card-sub { color: #666; font-size: .9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# SESSION STATE
# -----------------------------
if "homes" not in st.session_state:
    st.session_state.homes = []
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None
if "view_idx" not in st.session_state:
    st.session_state.view_idx = None

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

def make_thumb_src(info, photos_obj):
    urls = info.get("photo_urls") or []
    if urls:
        return urls[0]
    if photos_obj:
        b = photos_obj[0]["bytes"]
        b64 = base64.b64encode(b).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    # placeholder svg
    svg = """<svg xmlns='http://www.w3.org/2000/svg' width='800' height='450'>
      <rect width='100%' height='100%' fill='#f0f0f0'/>
      <text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='#888' font-size='24'>No Photo</text>
    </svg>"""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

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
            # Policy/fees
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
# FORM BUILDER
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

    return {
        "city": city, "community": community, "builder": builder, "address": address,
        "property_tax": tax, "mud": mud, "pid": pid, "hoa": hoa,
        "restrictions": restrictions, "hoa_includes": includes, "isp": isp,
        "schoolElem": schoolElem, "schoolMiddle": schoolMiddle, "schoolHigh": schoolHigh,
        "notes": notes, "photo_urls": [u.strip() for u in photo_urls_raw.split(",") if u.strip()],
        "uploads": [{"name": f.name, "type": f.type, "bytes": f.getbuffer().tobytes()} for f in (uploads or [])],
        "scores": scores,
    }

# -----------------------------
# TABS
# -----------------------------
tab_input, tab_props = st.tabs(["➕ Input", "🏘️ Properties"])

with tab_input:
    # Render Add or Edit form
    if st.session_state.edit_idx is not None:
        st.info("Editing an existing home")
        result = add_or_edit_form(st.session_state.edit_idx)
        c1, c2 = st.columns(2)
        if c1.button("Save changes"):
            idx = st.session_state.edit_idx
            st.session_state.homes[idx] = {
                "info": {k: result[k] for k in ["city","community","builder","address","property_tax","mud","pid","hoa","restrictions","hoa_includes","isp","schoolElem","schoolMiddle","schoolHigh","notes","photo_urls"]},
                "photos": result["uploads"],
                "scores": result["scores"],
            }
            st.success("Saved changes")
            st.session_state.edit_idx = None      # clear edit mode
            st.rerun()
        if c2.button("Cancel"):
            st.session_state.edit_idx = None
            st.rerun()
    else:
        result = add_or_edit_form(None)
        if st.button("Add Home"):
            st.session_state.homes.append({
                "info": {k: result[k] for k in ["city","community","builder","address","property_tax","mud","pid","hoa","restrictions","hoa_includes","isp","schoolElem","schoolMiddle","schoolHigh","notes","photo_urls"]},
                "photos": result["uploads"],
                "scores": result["scores"],
            })
            st.success(f"Added {result['address']}")

with tab_props:
    # DETAIL VIEW (only when view_idx is set and not editing)
    if st.session_state.view_idx is not None and st.session_state.edit_idx is None:
        i = st.session_state.view_idx
        if 0 <= i < len(st.session_state.homes):
            h = st.session_state.homes[i]
            info, scores = h["info"], h["scores"]
            st.markdown("#### 🏠 " + (info.get("address") or info.get("community") or "Home"))
            src = make_thumb_src(info, h.get("photos", []))
            st.markdown(f"<img class='thumb' style='height:320px;border-radius:14px;' src='{src}'/>", unsafe_allow_html=True)
            st.write(f"**City:** {info.get('city','')}  |  **MPC:** {info.get('community','')}  |  **Builder:** {info.get('builder','')}")
            st.write(f"**Overall:** {overall_score(scores)}  |  **Vaastu:** {vaastu_pass_count(scores)}/4")
            st.write(f"**Notes:** {info.get('notes','')}")
            st.markdown("##### Scores by Category")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write("**Environmental:**", category_subtotal(scores,"Environmental"))
                st.write("**Neighborhood:**", category_subtotal(scores,"Neighborhood"))
            with c2:
                st.write("**Community:**", category_subtotal(scores,"Community"))
                st.write("**Home:**", category_subtotal(scores,"Home"))
            with c3:
                st.write("**School:**", category_subtotal(scores,"School"))
                st.write("**Builder:**", category_subtotal(scores,"Builder"))
            st.markdown("---")
            st.write("**Costs & Policies:**")
            st.write(f"- Property Tax: {info.get('property_tax','')} | HOA (annual): {info.get('hoa','')}")
            st.write(f"- MUD: {info.get('mud','')} | PID: {info.get('pid','')}")
            st.write(f"- Restrictions: {info.get('restrictions','')}")
            st.write("**HOA Includes:** " + (", ".join([k for k,v in (info.get('hoa_includes',{}) or {}).items() if v]) or "—"))
            st.write(f"**ISP:** {info.get('isp','')}")
            st.write(f"**Zoned Schools:** {info.get('schoolElem','')} / {info.get('schoolMiddle','')} / {info.get('schoolHigh','')}")
            if st.button("⬅️ Back to Properties"):
                st.session_state.view_idx = None
                st.rerun()
        else:
            st.session_state.view_idx = None
            st.info("Listing not found.")
    else:
        st.markdown("### Your Properties")
        # CSV download for all
        if st.session_state.homes:
            df = homes_dataframe(st.session_state.homes)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Full Summary CSV", data=csv, file_name="home_summary.csv", mime="text/csv")

        # Grid: 3-column responsive-ish
        cols_per_row = 3
        for i, h in enumerate(st.session_state.homes):
            if i % cols_per_row == 0:
                row = st.columns(cols_per_row)
            col = row[i % cols_per_row]
            info, scores = h["info"], h["scores"]
            score = overall_score(scores)
            # thumbnail
            urls = info.get("photo_urls") or []
            if urls:
                src = urls[0]
            elif h.get("photos"):
                b = h["photos"][0]["bytes"]
                src = "data:image/png;base64," + base64.b64encode(b).decode("utf-8")
            else:
                src = "https://dummyimage.com/800x450/eeeeee/888888&text=No+Photo"
            with col:
                st.markdown(f"<div class='card'><img class='thumb' src='{src}' /><div class='badge-score'>{score}</div></div>", unsafe_allow_html=True)
                st.markdown(f"**{info.get('address','(no name)')}**")
                st.caption(f"{info.get('city','')} • {info.get('community','')} • {info.get('builder','')}")
                b1, b2, b3 = st.columns(3)
                if b1.button("View", key=f"v-{i}"):
                    st.session_state.view_idx = i     # set detail view
                    st.session_state.edit_idx = None  # clear edit
                    st.rerun()
                if b2.button("✏️ Edit", key=f"e-{i}"):
                    st.session_state.edit_idx = i     # set edit form
                    st.session_state.view_idx = None  # clear view
                    st.rerun()
                if b3.button("🗑️ Delete", key=f"d-{i}"):
                    del st.session_state.homes[i]     # delete this listing
                    st.rerun()

# -----------------------------
# VAASTU QUICK REFERENCE
# -----------------------------
st.markdown("---")
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
