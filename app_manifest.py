import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(layout="wide")

st.title("✈️ Aplikasi Konversi Manifest TXT")

st.markdown("Upload file manifest (.txt) → otomatis jadi tabel & summary")

# =========================
# UPLOAD
# =========================
file = st.file_uploader("Upload File Manifest", type=["txt"])

if file:

    text = file.read().decode("utf-8", errors="ignore")
    lines = text.split("\n")

    # =========================
    # HEADER INFO
    # =========================
    flight = re.search(r'FLIGHT:\s*(\S+\s*\d+)', text)
    date = re.search(r'DATE:\s*(\S+)', text)
    origin = re.search(r'PT.OF EMBARKATION:\s*(\S+)', text)
    dest = re.search(r'PT.OF DEST:\s*(\S+)', text)

    flight = flight.group(1) if flight else ""
    date = date.group(1) if date else ""
    origin = origin.group(1) if origin else ""
    dest = dest.group(1) if dest else ""

    st.info(f"Flight: {flight} | Date: {date} | {origin} → {dest}")

    # =========================
    # PARSING
    # =========================
    data = []

    for line in lines:

        # filter baris penumpang
        if re.match(r'\d{3}\s', line):

            try:
                parts = line.split("/")

                # nama
                nama = parts[0].split()
                lname = nama[1] if len(nama) > 1 else ""
                fname = nama[0]

                # jenis
                gender = parts[2].replace(".", "").strip()

                # seat
                seat = parts[3]

                # bag
                bag = parts[4].replace(".", "")
                bag = int(bag) if bag.isdigit() else 0

                # weight
                weight = parts[5].replace(".", "")
                weight = int(weight) if weight.isdigit() else 0

                # infant detect
                infant = "INF" in line

                data.append({
                    "Nama Depan": fname,
                    "Nama Belakang": lname,
                    "Jenis": gender,
                    "Seat": seat,
                    "Bagasi": bag,
                    "Berat": weight,
                    "Infant": 1 if infant else 0,
                    "Flight": flight,
                    "Tanggal": date,
                    "Asal": origin,
                    "Tujuan": dest
                })

            except:
                continue

    df = pd.DataFrame(data)

    # =========================
    # SUMMARY
    # =========================
    male = len(df[df["Jenis"] == "M"])
    female = len(df[df["Jenis"] == "F"])
    infant = df["Infant"].sum()

    bagasi = df["Bagasi"].sum()
    berat = df["Berat"].sum()

    total = len(df)

    st.subheader("📊 Summary")

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.metric("Total Pax", total)
    c2.metric("Male", male)
    c3.metric("Female", female)
    c4.metric("Infant", infant)
    c5.metric("Bagasi", bagasi)

    st.metric("Total Berat", berat)

    # =========================
    # TABLE
    # =========================
    st.subheader("📋 Data Penumpang")
    st.dataframe(df, use_container_width=True)

    # =========================
    # DOWNLOAD EXCEL
    # =========================
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='DATA')

        summary = pd.DataFrame({
            "Kategori": ["Total Pax","Male","Female","Infant","Bagasi","Berat"],
            "Jumlah": [total,male,female,infant,bagasi,berat]
        })

        summary.to_excel(writer, index=False, sheet_name='SUMMARY')

    st.download_button(
        "⬇️ Download Excel",
        data=output.getvalue(),
        file_name="manifest_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Silakan upload file manifest TXT")
