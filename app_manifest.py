import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(layout="wide")

st.title("✈️ Manifest TXT → Table + Summary (TR.ORG SMART FIX)")

file = st.file_uploader("Upload File Manifest (.txt)", type=["txt"])

if file:

    text = file.read().decode("utf-8", errors="ignore")
    lines = text.split("\n")

    # HEADER
    flight_match = re.search(r'FLIGHT:\s*([A-Z]{2,3}\s*\d+)', text)
    date_match = re.search(r'DATE:\s*(\S+)', text)
    origin_match = re.search(r'PT.OF EMBARKATION:\s*(\S+)', text)
    dest_match = re.search(r'PT.OF DEST:\s*(\S+)', text)

    main_flight = flight_match.group(1).replace(" ", "") if flight_match else ""
    date = date_match.group(1) if date_match else ""
    origin = origin_match.group(1) if origin_match else ""
    dest = dest_match.group(1) if dest_match else ""

    st.info(f"Flight: {main_flight} | Date: {date} | {origin} → {dest}")

    data = []

    for line in lines:

        if re.match(r'\d{3}\s', line):

            try:
                parts = line.split("/")

                # NAMA
                nama = parts[0].split()
                lname = nama[1] if len(nama) > 1 else ""
                fname = nama[0]

                # JENIS
                gender = parts[2].replace(".", "").strip()

                # SEAT
                seat = parts[3]

                # BAGASI
                bag = parts[4].replace(".", "")
                bag = int(bag) if bag.isdigit() else 0

                # BERAT
                weight = parts[5].replace(".", "")
                weight = int(weight) if weight.isdigit() else 0

                # =========================
                # 🔥 TR.ORG FIX CERDAS
                # =========================
                tr_org_raw = parts[9].strip() if len(parts) >= 10 else ""

                # bersihkan titik
                tr_org_clean = re.sub(r'\.+', '', tr_org_raw)

                # DETEKSI KODE FLIGHT
                is_flight_code = bool(re.match(r'^[A-Z]{2,3}\d{3,4}$', tr_org_clean))

                # LOGIC FINAL
                if tr_org_clean != "" and not is_flight_code:
                    is_transit = True
                else:
                    is_transit = False

                # NEXT FLIGHT (info saja)
                flights_found = re.findall(r'[A-Z]{2,3}\d{3,4}', line)
                flights_found = [f for f in flights_found if f != main_flight]
                next_flight = flights_found[0] if len(flights_found) > 0 else ""

                # TIPE PAX
                if "INF" in line:
                    pax_type = "INF"
                elif "CHD" in line:
                    pax_type = "CHD"
                else:
                    pax_type = "ADT"

                data.append({
                    "Nama Depan": fname,
                    "Nama Belakang": lname,
                    "Jenis": gender,
                    "Tipe Pax": pax_type,
                    "Seat": seat,
                    "Bagasi": bag,
                    "Berat": weight,
                    "Transit": "YA" if is_transit else "TIDAK",
                    "TR.ORG": tr_org_clean,
                    "Next Flight": next_flight,
                    "Flight": main_flight,
                    "Tanggal": date,
                    "Asal": origin,
                    "Tujuan": dest
                })

            except:
                continue

    df = pd.DataFrame(data)

    if df.empty:
        st.warning("Data tidak terbaca")
        st.stop()

    # =========================
    # SUMMARY
    # =========================
    total = len(df)
    adult = len(df[df["Tipe Pax"] == "ADT"])
    child = len(df[df["Tipe Pax"] == "CHD"])
    infant = len(df[df["Tipe Pax"] == "INF"])

    transit = len(df[df["Transit"] == "YA"])
    non_transit = len(df[df["Transit"] == "TIDAK"])

    bagasi = df["Bagasi"].sum()
    berat = df["Berat"].sum()

    st.subheader("📊 Summary")

    c1,c2,c3,c4,c5,c6 = st.columns(6)

    c1.metric("Total Pax", total)
    c2.metric("Adult", adult)
    c3.metric("Child", child)
    c4.metric("Infant", infant)
    c5.metric("Transit", transit)
    c6.metric("Non Transit", non_transit)

    st.metric("Bagasi", bagasi)
    st.metric("Total Berat", berat)

    st.subheader("📋 Data Penumpang")
    st.dataframe(df, use_container_width=True)

    # EXPORT
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='DATA')

    st.download_button(
        "⬇️ Download Excel",
        data=output.getvalue(),
        file_name="manifest_TRORG_SMART.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Upload file manifest TXT untuk mulai")
