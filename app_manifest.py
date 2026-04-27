import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(layout="wide")

st.title("✈️ Manifest TXT → Table + Summary (Transit = TR.ORG)")

# =========================
# UPLOAD
# =========================
file = st.file_uploader("Upload File Manifest (.txt)", type=["txt"])

if file:

    text = file.read().decode("utf-8", errors="ignore")
    lines = text.split("\n")

    # =========================
    # HEADER
    # =========================
    flight_match = re.search(r'FLIGHT:\s*([A-Z]{2,3}\s*\d+)', text)
    date_match = re.search(r'DATE:\s*(\S+)', text)
    origin_match = re.search(r'PT.OF EMBARKATION:\s*(\S+)', text)
    dest_match = re.search(r'PT.OF DEST:\s*(\S+)', text)

    main_flight = flight_match.group(1).replace(" ", "") if flight_match else ""
    date = date_match.group(1) if date_match else ""
    origin = origin_match.group(1) if origin_match else ""
    dest = dest_match.group(1) if dest_match else ""

    st.info(f"Flight: {main_flight} | Date: {date} | {origin} → {dest}")

    # =========================
    # PARSING
    # =========================
    data = []

    for line in lines:

        if re.match(r'\d{3}\s', line):

            try:
                parts = line.split("/")

                # ===== NAMA =====
                nama = parts[0].split()
                lname = nama[1] if len(nama) > 1 else ""
                fname = nama[0]

                # ===== JENIS =====
                gender = parts[2].replace(".", "").strip()

                # ===== SEAT =====
                seat = parts[3]

                # ===== BAGASI =====
                bag = parts[4].replace(".", "")
                bag = int(bag) if bag.isdigit() else 0

                # ===== BERAT =====
                weight = parts[5].replace(".", "")
                weight = int(weight) if weight.isdigit() else 0

                # =========================
                # 🔥 AMBIL TR.ORG (INDEX DINAMIS)
                # =========================
                tr_org = ""
                if len(parts) >= 10:
                    tr_org = parts[9].strip()

                # bersihkan nilai kosong
                if tr_org in ["", "...", "....", "....."]:
                    tr_org = ""

                # =========================
                # 🔥 LOGIC TRANSIT BARU
                # =========================
                is_transit = True if tr_org != "" else False

                # =========================
                # DETEKSI NEXT FLIGHT (OPSIONAL)
                # =========================
                flights_found = re.findall(r'[A-Z]{2,3}\d{3,4}', line)
                flights_found = [f for f in flights_found if f != main_flight]

                next_flight = flights_found[0] if len(flights_found) > 0 else ""

                # =========================
                # 🔥 DETEKSI TIPE PAX
                # =========================
                is_infant = "INF" in line
                is_child = "CHD" in line

                if is_infant:
                    pax_type = "INF"
                elif is_child:
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
                    "TR.ORG": tr_org,
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
        st.warning("Data tidak terbaca, cek format manifest")
        st.stop()

    # =========================
    # SUMMARY
    # =========================
    total = len(df)
    adult = len(df[df["Tipe Pax"] == "ADT"])
    child = len(df[df["Tipe Pax"] == "CHD"])
    infant = len(df[df["Tipe Pax"] == "INF"])

    male = len(df[df["Jenis"] == "M"])
    female = len(df[df["Jenis"] == "F"])

    transit = len(df[df["Transit"] == "YA"])
    non_transit = len(df[df["Transit"] == "TIDAK"])

    bagasi = df["Bagasi"].sum()
    berat = df["Berat"].sum()

    # =========================
    # KPI
    # =========================
    st.subheader("📊 Summary")

    c1,c2,c3,c4,c5,c6 = st.columns(6)

    c1.metric("Total Pax", total)
    c2.metric("Adult", adult)
    c3.metric("Child", child)
    c4.metric("Infant", infant)
    c5.metric("Transit", transit)
    c6.metric("Non Transit", non_transit)

    c7,c8 = st.columns(2)
    c7.metric("Bagasi", bagasi)
    c8.metric("Total Berat", berat)

    # =========================
    # TABLE
    # =========================
    st.subheader("📋 Data Penumpang")
    st.dataframe(df, use_container_width=True)

    # =========================
    # EXPORT EXCEL
    # =========================
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='DATA')

        summary = pd.DataFrame({
            "Kategori": [
                "Total Pax","Adult","Child","Infant",
                "Male","Female",
                "Transit","Non Transit",
                "Bagasi","Berat"
            ],
            "Jumlah": [
                total,adult,child,infant,
                male,female,
                transit,non_transit,
                bagasi,berat
            ]
        })

        summary.to_excel(writer, index=False, sheet_name='SUMMARY')

    st.download_button(
        "⬇️ Download Excel",
        data=output.getvalue(),
        file_name="manifest_TRORG.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Upload file manifest TXT untuk mulai")
