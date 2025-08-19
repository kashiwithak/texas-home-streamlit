import streamlit as st
import pandas as pd

st.set_page_config(page_title="Texas Home Tour Scoring", layout="wide")

# --- Session ---
if "homes" not in st.session_state:
    st.session_state.homes = []

# --- Tabs ---
tab1, tab2 = st.tabs(["➕ Input", "🏘️ Properties"])

# --------------------------------------------------
# INPUT TAB
# --------------------------------------------------
with tab1:
    st.title("🏡 Add / Edit Home")

    with st.form("add_home", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        address = c1.text_input("Address / Nickname*")
        city = c2.text_input("City")
        builder = c3.text_input("Builder")
        community = c4.text_input("Community")

        c5, c6, c7, c8 = st.columns(4)
        tax_rate = c5.text_input("Property Tax Rate")
        mud = c6.text_input("MUD")
        pid = c7.text_input("PID")
        hoa_fee = c8.text_input("Yearly HOA")

        st.markdown("**HOA Includes**")
        c9, c10, c11, c12, c13, c14 = st.columns(6)
        hoa_water = c9.checkbox("Water")
        hoa_sewer = c10.checkbox("Sewer")
        hoa_garbage = c11.checkbox("Garbage")
        hoa_gas = c12.checkbox("Gas")
        hoa_elec = c13.checkbox("Electric")
        hoa_internet = c14.checkbox("Internet")

        isp = st.text_input("ISP Provider")
        elem = st.text_input("Zoned Elementary")
        mid = st.text_input("Zoned Middle")
        high = st.text_input("Zoned High")

        notes = st.text_area("Notes")
        photo_url = st.text_input("Photo URL (main image)", placeholder="https://...")

        vaastu = st.checkbox("✅ Vaastu Pass")

        # Scoring categories
        st.subheader("Scores (1–5)")
        def slider(label, w=1):
            return st.slider(label, 1, 5, 3)
        scores = {
            "Environmental": slider("Environmental"),
            "Neighborhood": slider("Neighborhood"),
            "Community": slider("Community"),
            "Home": slider("Home"),
            "Builder": slider("Builder"),
            "School": slider("School"),
        }

        if st.form_submit_button("Save Home"):
            st.session_state.homes.append({
                "address": address,
                "city": city,
                "builder": builder,
                "community": community,
                "tax_rate": tax_rate,
                "mud": mud,
                "pid": pid,
                "hoa_fee": hoa_fee,
                "hoa_includes": {
                    "water": hoa_water,
                    "sewer": hoa_sewer,
                    "garbage": hoa_garbage,
                    "gas": hoa_gas,
                    "electric": hoa_elec,
                    "internet": hoa_internet,
                },
                "isp": isp,
                "elem": elem,
                "mid": mid,
                "high": high,
                "notes": notes,
                "photo_url": photo_url,
                "vaastu": vaastu,
                "scores": scores,
            })
            st.success(f"Added {address}")

# --------------------------------------------------
# PROPERTIES TAB
# --------------------------------------------------
with tab2:
    st.title("🏘️ Properties")

    if not st.session_state.homes:
        st.info("No homes added yet.")
    else:
        # Cards grid
        for i, h in enumerate(st.session_state.homes):
            with st.container():
                c1, c2 = st.columns([1,3])
                with c1:
                    if h["photo_url"]:
                        st.image(h["photo_url"], width=120)
                    else:
                        st.image("https://via.placeholder.com/120", width=120)
                with c2:
                    st.markdown(f"### {h['address']} ({h['city']})")
                    st.write(f"🏗️ {h['builder']} | 🏘️ {h['community']}")
                    st.write(f"**Total Score:** {sum(h['scores'].values())}/30")
                    st.write(f"Notes: {h['notes']}")
        # CSV Export
        if st.button("⬇️ Export CSV"):
            df = pd.DataFrame([{
                **h,
                **{f"score_{k}": v for k,v in h["scores"].items()}
            } for h in st.session_state.homes])
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "homes.csv", "text/csv")
