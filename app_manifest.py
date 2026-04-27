import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(layout="wide")

st.title("✈️ Manifest TXT → Table + Summary (FINAL STABLE TR.ORG)")

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
                bag = int(parts[4].replace(".", "")) if parts[4].replace(".", "").isdigit() else 0

                # BERAT
                weight = int(parts[5].replace(".", "")) if parts[5].replace(".", "").isdigit() else 0

                # =========================
                # 🔥 DETEKSI TR.ORG BERDASARKAN POLA
                # =========================
                tokens = parts

                tr_org_clean = ""

                for t in tokens:
                    t_clean = re.sub(r'\.+', '', t).strip()

                    # cek kode bandara (3 huruf)
                    if re.match(r'^[A-Z]{3}$', t_clean):
                        tr_org_clean = t_clean
                        break

                # LOGIC TRANSIT
                is_transit = True if tr_org_clean != "" else False

                # =========================
                # NEXT FLIGHT
                # =========================
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

    st.subheader("📊 Summary")

    c1,c2,c3,c4,c5,c6 = st.columns(6)

    c1.metric("Total Pax", len(df))
    c2.metric("Adult", len(df[df["Tipe Pax"]=="ADT"]))
    c3.metric("Child", len(df[df["Tipe Pax"]=="CHD"]))
    c4.metric("Infant", len(df[df["Tipe Pax"]=="INF"]))
    c5.metric("Transit", len(df[df["Transit"]=="YA"]))
    c6.metric("Non Transit", len(df[df["Transit"]=="TIDAK"]))

    st.metric("Bagasi", df["Bagasi"].sum())
    st.metric("Berat", df["Berat"].sum())

    st.subheader("📋 Data Penumpang")
    st.dataframe(df, use_container_width=True)

    # EXPORT
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)

    st.download_button("⬇️ Download Excel", data=output.getvalue(),
                       file_name="manifest_final_stable.xlsx")

else:
    st.info("Upload file manifest TXT untuk mulai")
