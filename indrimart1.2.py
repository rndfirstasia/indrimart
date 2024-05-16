import streamlit as st
import pandas as pd
import gspread
from streamlit_gsheets import GSheetsConnection
from datetime import date

st.set_page_config(page_title="Indrimart", page_icon="favicon.png")

conn = st.connection("gsheets_cloud", type=GSheetsConnection)

# List harga makanan
harga_makanan = {
    "Jardin Coffe/Tea": 13000,
    "Susu Bear Brand": 10500,
    "Cimory Pouch": 10000,
    "Oatside Coffee": 9500,
    "Oatside Choco/Barista": 10000,
    "Oatside with straw (Choco/Barista/Coffee)": 6500,
    "Oatside with straw Choco Malt": 5500,
    "You C1000": 7500,
    "Hydro Coco": 7500,
    "Nescafe Coffee Creamer": 5000,
    "Susu Ultra": 3500,

    "Oreo": 2000,
    "Good Time": 2000,
    "Beng-Beng": 2000,
    "Roma Sari Gandum": 2000,
    "Choki-choki Stick": 2000,
    "Apetito": 2000,
    "Nyam Nyam": 2000,
    "Roma Malkist Crackers": 1000,
    "Choki Choki Pasta": 1000,
    "Superstar": 1000,
    "Roka": 1000,

    "Sosis Kanzler (All Varian)": 9000,
    "Mie Gemez/Mi Kremez": 1000,
    "Kacang Garuda (All Varian)": 1000,
    "Chuba": 1000,
    "Tricks": 1000
}

user_sheet = {
    "Pilih User":"Pilih User",
    "Ara": "Ara",
    "Adhit": "Adhit",
    "Nafi": "Nafi",
    "Rasyid": "Rasyid",
    "Saleh": "Saleh",
    "Wisnu": "Wisnu",
    "Abi": "Abi",
    "Catur": "Catur",
    "Galant": "Galant",
    "Lukman": "Lukman",
    "Nugraha": "Nugraha",
    "Gofur": "Gofur",
    "Luthfi": "Luthfi"
}

# Logo
col1, col2, col3 = st.columns([1,6,1])
with col2:
    st.image("hero.jpg", use_column_width=True)

user_name = st.selectbox("Siapa Anda?", list(user_sheet.keys()))
user_key = user_sheet[user_name]
url = "https://docs.google.com/spreadsheets/d/145gkOwB6JCLDtvOkt7YhRi8EnSRl7qYuYd-3lMop02M/edit?usp=sharing"
df = conn.read(spreadsheet=url, worksheet=user_key, usecols=list(range(4)))

# Tab
tab1, tab2, tab3 = st.tabs(["Nyemil Nyam Nyam Nyam~", "Belanjaan", "Daftar Harga"])

def tambah_data_belanja(df, tanggal, makanan, jumlah, total_harga):
    new_row = {"Tanggal": tanggal, "Makanan": makanan, "Jumlah": jumlah, "Total Harga": total_harga}
    df = df.append(new_row, ignore_index=True)
    return df

with tab1:
    # Fungsi untuk menghitung total harga
    def hitung_total_harga(makanan, jumlah):
        return harga_makanan[makanan] * jumlah

    df = df.dropna(how='all')

    # Inisialisasi DataFrame
    if "data" not in st.session_state:
        st.session_state.data = df #pd.DataFrame(columns=["Tanggal", "Makanan", "Jumlah", "Total Harga"])

    with st.container(border=True):
        # Input data
        tanggal = st.date_input("Tanggal", date.today())
        makanan = st.selectbox("Pilih Makanan/Minuman", list(harga_makanan.keys()))
        jumlah = st.number_input("Pcs", min_value=1, step=1)
        total_harga = hitung_total_harga(makanan, jumlah)

        # Tampilkan total harga
        st.write(f"Jumlah: Rp{total_harga}")

        # Submit button
        if st.button("Tambah"):
            new_data = {"Tanggal": str(tanggal), "Makanan": makanan, "Jumlah": jumlah, "Total Harga": total_harga}
            st.session_state.data = st.session_state.data.append(new_data, ignore_index=True)
            conn.update(worksheet=user_key, data=st.session_state.data)
            st.success("Belanja berhasil dicatat!")

    # Fungsi untuk menghapus baris
    def hapus_baris():
        indices_to_drop = [i for i, row in enumerate(st.session_state.data.iterrows()) if st.session_state[f'delete_{i}']]
        st.session_state.data.drop(indices_to_drop, inplace=True)
        conn.update(worksheet=user_key, data=st.session_state.data)
        st.session_state.data.reset_index(drop=True, inplace=True)

with tab2:
    # Show data in the DataFrame
    if not st.session_state.data.empty:
        cols = st.columns([1, 2, 2, 2, 2, 1])
        headers = ["No.", "Tanggal", "Makanan", "Jumlah", "Total Harga", "Hapus"]
        for col, header in zip(cols, headers):
            col.write(header)
        
        for i, row in st.session_state.data.iterrows():
            cols = st.columns([1, 2, 2, 2, 2, 1])
            cols[0].write(i + 1)
            cols[1].write(row["Tanggal"])
            cols[2].write(row["Makanan"])
            cols[3].write(row["Jumlah"])
            cols[4].write(row["Total Harga"])
            cols[5].checkbox("", key=f"delete_{i}")

        if st.button("Hapus Baris yang Dipilih"):
            hapus_baris()
            st.experimental_rerun()
        
        # Calculate and display total harga
        total_harga_sum = st.session_state.data["Total Harga"].sum()
        st.subheader(f"**Total Belanjaan: Rp. {total_harga_sum}**")

    else:
        st.write("Tidak ada data yang dicatat.")

with tab3:
    df_harga_makanan = pd.DataFrame(list(harga_makanan.items()), columns=['Makanan & Minuman', 'Harga'])

    st.table(df_harga_makanan)

    st.write("Pembayaran:")
    st.write("0840882420")
    st.write("a.n. LAY LI NIE")