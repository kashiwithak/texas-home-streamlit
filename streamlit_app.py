
import streamlit as st
import pandas as pd
import base64
from streamlit import components

# =============================
# CONFIG: criteria + weights
# =============================
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
  # Vaastu (deal-breakers as pass/fail -> 5 or 0)
  ("Vaastu", "Main Entrance (East/North ✅, South ❌)", 5),
  ("Vaastu", "Kitchen (SE/NW ✅, NE ❌)", 4),
  ("Vaastu", "Master Bedroom (SW ✅, NE ❌)", 4),
  ("Vaastu", "Pooja Room (NE/E ✅, South/under stairs ❌)", 3),
]
CATEGORIES = ["Environmental","Neighborhood","Community","Home","Builder","School","Vaastu"]

# =============================
# PAGE CONFIG + STYLES
# =============================
st.set_page_config(page_title="Texas Home Tour Scoring", layout="wide")
st.title("🏡 Texas Home Tour Scoring")

st.markdown(
    """
    <style>
      .block-container { padding-top: .6rem; padding-bottom: 2rem; }
      .stButton>button, .stDownloadButton>button { padding: 0.5rem 0.9rem; border-radius: 10px; }
      /* Responsive card grid */
      .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
      @media (max-width: 1200px) { .grid { grid-template-columns: repeat(3, 1fr); } }
      @media (max-width: 900px)  { .grid { grid-template-columns: repeat(2, 1fr); } }
      @media (max-width: 600px)  { .grid { grid-template-columns: 1fr; } }
      .card-wrap { position: relative; }
      .card { position: relative; overflow: hidden; border-radius: 14px; border: 1px solid #e6e6e6; }
      .thumb { width: 100%; height: 220px; object-fit: cover; display: block; }
      @media (max-width: 768px) { .thumb { height: 160px; } }
      .badge-score { position: absolute; left: 10px; top: 10px; background: rgba(0,0,0,.8); color: #fff; padding: 6px 10px; border-radius: 999px; font-size: 0.85rem; z-index: 2; }
      .badge-actions { position: absolute; right: 10px; top: 10px; display: flex; gap: 8px; z-index: 3; }
      .pill { background: rgba(255,255,255,.95); color: #111; padding: 6px 10px; border-radius: 999px; font-size: 0.85rem; border: 1px solid #ddd; text-decoration: none; }
      .card-title { font-weight: 600; margin-top: .35rem; }
      .card-sub { color: #666; font-size: .9rem; }
      .cover-link { position:absolute; inset:0; display:block; z-index:1; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================
# SESSION STATE
# =============================
if "homes" not in st.session_state:
    st.session_state.homes = []
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None
if "view_idx" not in st.session_state:
    st.session_state.view_idx = None

# =============================
# HELPERS
# =============================
def criterion_key(cat, name):
    return f"{cat}::{name}"

def category_subtotal(scores, category):
    return sum(scores.get(criterion_key(c_cat,name), 0) * weight
               for (c_cat, name, weight) in CRITERIA if c_cat == category)

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
            # Tax/fees/policies
            "PropertyTax": info.get("property_tax",""),
            "MUD": "Yes" if info.get("mud_has") else "No",
            "MUD_Details": info.get("mud_details",""),
            "PID": "Yes" if info.get("pid_has") else "No",
            "PID_Details": info.get("pid_details",""),
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
            "Address/Nickname": info.get("address",""),
        })
    return pd.DataFrame(rows)

# =============================
# ADD / EDIT FORM (full)
# =============================
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
        address = st.text_input("Address/Nickname*", value=info.get("address",""))

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        tax = st.text_input("Property Tax Rate", value=info.get("property_tax",""))
    with c6:
        mud_has = st.checkbox("MUD present?", value=info.get("mud_has", False))
    with c7:
        pid_has = st.checkbox("PID present?", value=info.get("pid_has", False))
    with c8:
        hoa = st.text_input("Yearly HOA ($)", value=info.get("hoa",""))

    d1, d2 = st.columns(2)
    with d1:
        mud_details = st.text_input("MUD details/rate (optional)", value=info.get("mud_details",""), disabled=not mud_has)
    with d2:
        pid_details = st.text_input("PID details/rate (optional)", value=info.get("pid_details",""), disabled=not pid_has)

    restrictions = st.text_area("Restrictions", value=info.get("restrictions",""))
    st.markdown("**HOA Includes:**")
    hoa_cols = st.columns(6)
    includes = {}
    for i, field in enumerate(["Water","Sewer","Garbage","Gas","Electric","Internet"]):
        includes[field] = hoa_cols[i].checkbox(field, value=info.get("hoa_includes",{}).get(field, False))

    isp = st.text_input("ISP Provider", value=info.get("isp",""))

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        schoolElem = st.text_input("Zoned Elementary", value=info.get("schoolElem",""))
    with sc2:
        schoolMiddle = st.text_input("Zoned Middle", value=info.get("schoolMiddle",""))
    with sc3:
        schoolHigh = st.text_input("Zoned High (optional)", value=info.get("schoolHigh",""))

    notes = st.text_area("Notes", value=info.get("notes",""))

    photo_urls_raw = st.text_input("Photo URLs (comma-separated)", value=",".join(info.get("photo_urls",[])))
    uploads = st.file_uploader("Upload photos", type=["png","jpg","jpeg","webp"], accept_multiple_files=True)

    # Scores
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
        "property_tax": tax, "mud_has": mud_has, "mud_details": mud_details,
        "pid_has": pid_has, "pid_details": pid_details, "hoa": hoa,
        "restrictions": restrictions, "hoa_includes": includes, "isp": isp,
        "schoolElem": schoolElem, "schoolMiddle": schoolMiddle, "schoolHigh": schoolHigh,
        "notes": notes, "photo_urls": [u.strip() for u in photo_urls_raw.split(",") if u.strip()],
        "uploads": [{"name": f.name, "type": f.type, "bytes": f.getbuffer().tobytes()} for f in (uploads or [])],
        "scores": scores,
    }

# =============================
# QUERY PARAMS (clickable card actions)
# =============================
qp = st.query_params
def consume_idx_param(name):
    if name in qp:
        try:
            raw = qp[name]
            val = raw[0] if isinstance(raw, list) else raw
            idx = int(val)
        except Exception:
            idx = None
        try:
            del st.query_params[name]
        except Exception:
            pass
        return idx
    return None

# Delete -> Edit -> View
del_idx = consume_idx_param("delete")
if del_idx is not None:
    if 0 <= del_idx < len(st.session_state.homes):
        st.session_state.homes.pop(del_idx)
    st.rerun()

ed_idx = consume_idx_param("edit")
if ed_idx is not None and 0 <= ed_idx < len(st.session_state.homes):
    st.session_state.edit_idx = ed_idx
    st.session_state.view_idx = None

vw_idx = consume_idx_param("view")
if vw_idx is not None and 0 <= vw_idx < len(st.session_state.homes):
    st.session_state.view_idx = vw_idx
    st.session_state.edit_idx = None

# =============================
# TABS: Input / Properties
# =============================
tab_input, tab_props = st.tabs(["➕ Input", "🏘️ Properties"])

with tab_input:
    if st.session_state.edit_idx is not None:
        st.info("Editing an existing home")
        result = add_or_edit_form(st.session_state.edit_idx)
        c1, c2 = st.columns(2)
        if c1.button("Save changes"):
            idx = st.session_state.edit_idx
            st.session_state.homes[idx] = {
                "info": {k: result[k] for k in ["city","community","builder","address","property_tax","mud_has","mud_details","pid_has","pid_details","hoa","restrictions","hoa_includes","isp","schoolElem","schoolMiddle","schoolHigh","notes","photo_urls"]},
                "photos": result["uploads"],
                "scores": result["scores"],
            }
            st.success("Saved changes")
            st.session_state.edit_idx = None
            st.rerun()
        if c2.button("Cancel"):
            st.session_state.edit_idx = None
            st.rerun()
    else:
        result = add_or_edit_form(None)
        if st.button("Add Home"):
            if not result["address"].strip():
                st.warning("Please enter an address/nickname.")
            else:
                st.session_state.homes.append({
                    "info": {k: result[k] for k in ["city","community","builder","address","property_tax","mud_has","mud_details","pid_has","pid_details","hoa","restrictions","hoa_includes","isp","schoolElem","schoolMiddle","schoolHigh","notes","photo_urls"]},
                    "photos": result["uploads"],
                    "scores": result["scores"],
                })
                st.success(f"Added {result['address']}")

with tab_props:
    if st.session_state.view_idx is not None and st.session_state.edit_idx is None:
        i = st.session_state.view_idx
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
        mud_text = "Yes" if info.get('mud_has') else "No"
        pid_text = "Yes" if info.get('pid_has') else "No"
        st.write(f"- Property Tax: {info.get('property_tax','')} | HOA (annual): {info.get('hoa','')}")
        st.write(f"- MUD: {mud_text} {('(' + info.get('mud_details','') + ')') if info.get('mud_details') else ''} | PID: {pid_text} {('(' + info.get('pid_details','') + ')') if info.get('pid_details') else ''}")
        st.write(f"- Restrictions: {info.get('restrictions','')}")
        st.write("**HOA Includes:** " + (", ".join([k for k,v in (info.get('hoa_includes',{}) or {}).items() if v]) or "—"))
        st.write(f"**ISP:** {info.get('isp','')}")
        st.write(f"**Zoned Schools:** {info.get('schoolElem','')} / {info.get('schoolMiddle','')} / {info.get('schoolHigh','')}")
        st.markdown("---")
        if st.button("⬅️ Back to list"):
            st.session_state.view_idx = None
            st.rerun()
    else:
        st.markdown("### Your Properties")
        if st.session_state.homes:
            df = homes_dataframe(st.session_state.homes)
            st.download_button("📥 Download Full Summary CSV", data=df.to_csv(index=False).encode("utf-8"),
                               file_name="home_summary.csv", mime="text/csv")

        # Build HTML without leading indentation; render via components.html to avoid markdown code-blocking
        cards_html = "<div class='grid'>"
        for i, h in enumerate(st.session_state.homes):
            info, scores = h["info"], h["scores"]
            score = overall_score(scores)
            src = make_thumb_src(info, h.get("photos", []))
            title = info.get('address','(no name)')
            sub = f"{info.get('city','')} • {info.get('community','')} • {info.get('builder','')}"
            cards_html += (
                "<div class='card-wrap'>"
                f"<a class='cover-link' href='?view={i}'></a>"
                "<div class='card'>"
                f"<img class='thumb' src='{src}' />"
                f"<div class='badge-score'>{score}</div>"
                "<div class='badge-actions'>"
                f"<a class='pill' href='?edit={i}'>✏️ Edit</a>"
                f"<a class='pill' href='?delete={i}'>🗑️ Delete</a>"
                "</div>"
                "</div>"
                f"<div class='card-title'>{title}</div>"
                f"<div class='card-sub'>{sub}</div>"
                "</div>"
            )
        cards_html += "</div>"
        rows = max(1, (len(st.session_state.homes) + 3) // 4)
        height = min(1400, 320 + rows * 320)
        components.v1.html(cards_html, height=height, scrolling=True)

# =============================
# VAASTU QUICK REFERENCE
# =============================
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
