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
        row = {
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
            "PropertyTax": info.get("property_tax",""),
            "MUD": info.get("mud",""),
            "PID": info.get("pid",""),
            "YearlyHOA": info.get("hoa",""),
            "Restrictions": info.get("restrictions",""),
            "ISP": info.get("isp",""),
            "ZonedElem": info.get("schoolElem",""),
            "ZonedMid": info.get("schoolMiddle",""),
            "ZonedHigh": info.get("schoolHigh",""),
            "Address/Nickname": info.get("address",""),
        }
        rows.append(row)
    return pd.DataFrame(rows)

# -----------------------------
# ADD / EDIT FORM
# -----------------------------
def add_or_edit_form(edit_idx=None):
    is_edit = edit_idx is not None
    st.subheader("Edit Home" if is_edit else "Add a Home")

    # load existing values if editing
    info = {}
    prev_scores = {}
    if is_edit:
        info = st.session_state.homes[edit_idx]["info"].copy()
        prev_scores = st.session_state.homes[edit_idx]["scores"].copy()

    city = st.text_input("City", value=info.get("city",""))
    community = st.text_input("MPC / Community", value=info.get("community",""))
    builder = st.text_input("Builder", value=info.get("builder",""))
    address = st.text_input("Address/Nickname", value=info.get("address",""))
    tax = st.text_input("Property Tax Rate", value=info.get("property_tax",""))
    mud = st.text_input("MUD", value=info.get("mud",""))
    pid = st.text_input("PID", value=info.get("pid",""))
    hoa = st.text_input("Yearly HOA ($)", value=info.get("hoa",""))
    restrictions = st.text_area("Restrictions", value=info.get("restrictions",""))

    st.markdown("**HOA Includes:**")
    includes = {}
    for field in ["Water","Sewer","Garbage","Gas","Electric","Internet"]:
        includes[field] = st.checkbox(field, value=info.get("hoa_includes",{}).get(field, False))

    isp = st.text_input("ISP Provider", value=info.get("isp",""))
    schoolElem = st.text_input("Zoned Elementary", value=info.get("schoolElem",""))
    schoolMiddle = st.text_input("Zoned Middle", value=info.get("schoolMiddle",""))
    schoolHigh = st.text_input("Zoned High (optional)", value=info.get("schoolHigh",""))
    notes = st.text_area("Notes", value=info.get("notes",""))

    photo_urls_raw = st.text_input("Photo URLs (comma-separated)", value=",".join(info.get("photo_urls",[])))

    scores = {}
    for cat in CATEGORIES:
        st.markdown(f"### {cat}")
        for (c_cat, name, weight) in [c for c in CRITERIA if c[0] == cat]:
            key = criterion_key(c_cat,name)
            if c_cat == "Vaastu":
                default = bool(prev_scores.get(key, 0) >= 5) if is_edit else False
                val = st.checkbox(name, value=default)
                scores[key] = 5 if val else 0
            else:
                default = int(prev_scores.get(key, 3)) if is_edit else 3
                val = st.slider(f"{name} (Weight {weight})", 1, 5, default)
                scores[key] = val

    if is_edit:
        if st.button("Save changes"):
            st.session_state.homes[edit_idx] = {
                "info": {
                    "city": city, "community": community, "builder": builder, "address": address,
                    "property_tax": tax, "mud": mud, "pid": pid, "hoa": hoa,
                    "restrictions": restrictions, "hoa_includes": includes,
                    "isp": isp, "schoolElem": schoolElem, "schoolMiddle": schoolMiddle, "schoolHigh": schoolHigh,
                    "notes": notes, "photo_urls": [u.strip() for u in photo_urls_raw.split(",") if u.strip()],
                },
                "scores": scores,
            }
            st.session_state.edit_idx = None
            st.success("Updated home")
            st.experimental_rerun()
    else:
        if st.button("Add Home"):
            st.session_state.homes.append({
                "info": {
                    "city": city, "community": community, "builder": builder, "address": address,
                    "property_tax": tax, "mud": mud, "pid": pid, "hoa": hoa,
                    "restrictions": restrictions, "hoa_includes": includes,
                    "isp": isp, "schoolElem": schoolElem, "schoolMiddle": schoolMiddle, "schoolHigh": schoolHigh,
                    "notes": notes, "photo_urls": [u.strip() for u in photo_urls_raw.split(",") if u.strip()],
                },
                "scores": scores,
            })
            st.success(f"Added {address}")
            st.experimental_rerun()

# -----------------------------
# MAIN
# -----------------------------
if st.session_state.edit_idx is not None:
    add_or_edit_form(st.session_state.edit_idx)
else:
    with st.expander("➕ Add a Home"):
        add_or_edit_form()

    st.subheader("Quick Summary")
    if st.session_state.homes:
        df = homes_dataframe(st.session_state.homes)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No homes yet. Use 'Add a Home'.")

# -----------------------------
# Quick Reference Notes (Vaastu)
# -----------------------------
st.markdown("## 🧭 Vaastu Quick Reference")
st.markdown("""
**Primary Dealbreakers (Pass/Fail criteria):**
- **Main Entrance**: East/North ✅, South ❌
- **Kitchen**: Southeast or Northwest ✅, Northeast ❌
- **Master Bedroom**: Southwest ✅, Northeast ❌
- **Pooja Room**: Northeast/East ✅, South or under stairs ❌

**Secondary Considerations (Reference only):**
- Toilets not in NE
- Stairs not in NE
- Water tanks ideally in NW
- Slope of site should be North or East
""")
