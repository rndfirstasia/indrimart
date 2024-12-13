import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import date
import os

# ENVIRONMENT
mysql_user = st.secrets["mysql"]["username"]
mysql_password = st.secrets["mysql"]["password"]
mysql_host = st.secrets["mysql"]["host"]
mysql_port = st.secrets["mysql"]["port"]
mysql_database = st.secrets["mysql"]["database"]

st.set_page_config(page_title="Indrimart", page_icon="favicon.png")

# MySQL Connection
def create_db_connection():
    try:
        conn = mysql.connector.connect(
            user=mysql_user,
            password=mysql_password,
            host=mysql_host,
            port=mysql_port,
            database=mysql_database
        )
        if conn.is_connected():
            return conn
    except Error as e:
        st.error(f"Database connection failed: {e}")
        return None

# Fetch data from database
def fetch_data(query, params=None):
    conn = create_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
        finally:
            conn.close()
        return results
    return []

# Insert or update data into database
def execute_query(query, data=None):
    conn = create_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            if data:
                cursor.execute(query, data)
            else:
                cursor.execute(query)
            conn.commit()
        except Error as e:
            st.error(f"Database operation failed: {e}")
        finally:
            conn.close()

# Fetch harga makanan
def get_daftar_harga_makanan():
    query = "SELECT nama, harga, img FROM indrimart_produk"
    return {row['nama']: (row['harga'], row['img']) for row in fetch_data(query)}

# Fetch transaksi user
def get_user_transaksi(user_name):
    query = """
    SELECT
        indrimart_belanjaan.belanjaan_id,
        indrimart_belanjaan.tanggal AS "tanggal",
        indrimart_produk.nama AS "produk",
        indrimart_belanjaan.total_harga AS "total_harga",
        indrimart_belanjaan.jumlah AS "jumlah"
    FROM indrimart_belanjaan 
    JOIN indrimart_login ON indrimart_login.user_id = indrimart_belanjaan.user_id
    JOIN indrimart_produk ON indrimart_belanjaan.produk_id = indrimart_produk.produk_id
    WHERE username = %s AND is_paid = 0 ORDER BY tanggal DESC
    """
    return fetch_data(query, (user_name,))

# Add transaksi
def add_transaksi(user_id, produk_id, tanggal, jumlah, total_harga, is_paid=False):
    query = """
        INSERT INTO indrimart_belanjaan (user_id, produk_id, tanggal, jumlah, total_harga, is_paid)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    execute_query(query, (user_id, produk_id, tanggal, jumlah, total_harga, is_paid))

# Delete transaksi
def delete_transaksi(transaksi_id):
    query = "DELETE FROM indrimart_belanjaan WHERE user_id = %s"
    execute_query(query, (transaksi_id,))

def get_user_id(user_name):
    query = """
    SELECT user_id FROM indrimart_login WHERE username = %s
    """
    results = fetch_data(query, (user_name,))
    return results[0]['user_id'] if results else None

def validasi_login(username, password):
    query = "SELECT * FROm indrimart_login WHERE username = %s AND password = %s"
    results = fetch_data(query, (username, password))
    return results[0] if results else None

def terbayarkan(belanjaan_id):
    query = "UPDATE indrimart_belanjaan SET is_paid = 1 WHERE belanjaan_id = %s"
    execute_query(query, (belanjaan_id,))

def delete_transaksi(belanjaan_id):
    query = "DELETE FROM indrimart_belanjaan WHERE belanjaan_id = %s"
    execute_query(query, (belanjaan_id,))

def get_riwayat_belanja(user_name):
    query = """
    SELECT
        indrimart_belanjaan.tanggal AS "tanggal",
        indrimart_produk.nama AS "produk",
        indrimart_belanjaan.jumlah AS "jumlah",
        indrimart_belanjaan.total_harga AS "total_harga"
    FROM indrimart_belanjaan
    JOIN indrimart_login ON indrimart_login.user_id = indrimart_belanjaan.user_id
    JOIN indrimart_produk ON indrimart_belanjaan.produk_id = indrimart_produk.produk_id
    WHERE username = %s AND is_paid = 1 ORDER BY tanggal DESC
    """
    return fetch_data(query, (user_name,))

def ubah_password(user_id, password_baru):
    query = "UPDATE indrimart_login SET password = %s WHERE user_id = %s"
    execute_query(query, (password_baru, user_id))

def validasi_password_lama(username, password):
    user = validasi_login(username, password)
    return user is not None

# Data harga makanan
harga_makanan = get_daftar_harga_makanan()

def tampilkan_gambar_produk(makanan):
    product_info = harga_makanan.get(makanan)
    
    if product_info:
        price, image_file = product_info
        image_path = os.path.join("img", image_file)
        
        if os.path.exists(image_path):
            st.image(image_path, use_container_width=True)
        else:
            st.warning("Gambar produk tidak tersedia.")
    else:
        st.warning("Produk tidak ditemukan dalam daftar harga.")

def get_produk_id_by_nama(nama_produk):
    query = "SELECT produk_id FROM indrimart_produk WHERE nama = %s"
    result = fetch_data(query, (nama_produk,))
    return result[0]['produk_id'] if result else None

# Logo
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.image("hero.jpg", use_container_width=True)

# Fungsi untuk menampilkan modal ubah password
@st.dialog("Ubah Password")
def modal_ubah_password(user_id, username):
    st.write("Silakan ubah password Anda:")
    password_lama = st.text_input("Password Lama:", type="password", key="old_password")
    password_baru = st.text_input("Password Baru:", type="password", key="new_password")
    konfirmasi_password = st.text_input("Konfirmasi Password Baru:", type="password", key="confirm_password")

    if st.button("Simpan"):
        if not password_lama or not password_baru or not konfirmasi_password:
            st.error("Semua kolom harus diisi.")
        elif password_baru != konfirmasi_password:
            st.error("Password baru dan konfirmasi tidak cocok.")
        elif not validasi_password_lama(username, password_lama):
            st.error("Password lama tidak sesuai.")
        else:
            ubah_password(user_id, password_baru)
            st.success("Password berhasil diubah!")
            st.session_state["show_change_password"] = False # sembunyikan dialog kalau dah slese
            st.rerun()

if "username" not in st.session_state:
    st.session_state.username = ""
if "password" not in st.session_state:
    st.session_state.password = ""
if "temp_username" not in st.session_state:
    st.session_state.temp_username = ""
if "temp_password" not in st.session_state:
    st.session_state.temp_password = ""
if "show_change_password" not in st.session_state:
    st.session_state.show_change_password = False 

if not st.session_state.username and not st.session_state.password:
    # User login
    # user_name = st.text_input("Username", value=st.session_state.temp_username, key="username")
    # password = st.text_input("Password", type="password", value=st.session_state.temp_password, key="password")

    st.session_state.temp_username = st.text_input("Username", value=st.session_state.temp_username)
    st.session_state.temp_password = st.text_input("Password", type="password", value=st.session_state.temp_password)

    if st.session_state.temp_username and st.session_state.temp_password:
        user = validasi_login(st.session_state.temp_username, st.session_state.temp_password)
        if user:
            st.session_state.username = st.session_state.temp_username
            st.session_state.password = st.session_state.temp_password
            st.rerun() 
        else:
            st.error("Username atau password salah.")
else:
    st.subheader(f"Selamat datang, {st.session_state.username}!")

    if st.button("🔑 Ubah Password"):
        st.session_state.show_change_password = True

    if st.session_state.show_change_password:
        modal_ubah_password(user_id=1, username=st.session_state.username) 

# Tab layout
tab3, tab1, tab2  = st.tabs(["Daftar Harga", "Belanja", "Riwayat Belanja"])

if st.session_state.username and st.session_state.password:
    user = validasi_login(st.session_state.username, st.session_state.password)
    if user:
        user_id = user['user_id']

        with tab1:
            st.subheader("💸 Belanja")
            st.info('Anda dapat menambahkan item yang Anda beli')
            def hitung_total_harga(makanan, jumlah):
                harga, _ = harga_makanan.get(makanan, (0, ""))
                return harga * jumlah

            if st.session_state.username:
                user_id = get_user_id(st.session_state.username)
                if user_id:
                    # Input data
                    with st.container(border=True):
                        col1, col2 = st.columns([6, 4])
                        with col1:
                            tanggal = st.date_input("Tanggal", date.today())
                            # Ubah format tanggal
                            formatted_tanggal = tanggal.strftime("%d %B %Y")
                            bulan_dict = {
                                "January": "Januari", "February": "Februari", "March": "Maret", "April": "April", 
                                "May": "Mei", "June": "Juni", "July": "Juli", "August": "Agustus", 
                                "September": "September", "October": "Oktober", "November": "November", "December": "Desember"
                            }
                            for english_month, indonesian_month in bulan_dict.items():
                                formatted_tanggal = formatted_tanggal.replace(english_month, indonesian_month)

                            makanan = st.selectbox("Pilih Makanan/Minuman", list(harga_makanan.keys()))
                            jumlah = st.number_input("Jumlah (pcs)", min_value=1, step=1)
                        with col2:
                            tampilkan_gambar_produk(makanan)

                        col1, col2 = st.columns([7, 3])
                        total_harga = hitung_total_harga(makanan, jumlah)
                        with col1:
                            total_harga = int(total_harga)
                            formatted_total_harga = f"{total_harga:,.0f}"
                            st.markdown(
                                """
                                <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                                    <!-- Your content here -->
                                    <h3>Total: Rp.{}</h3>
                                </div>
                                """.format(formatted_total_harga),
                                unsafe_allow_html=True,
                            )
                        with col2:
                            # Tambah data
                            if st.button("➕ Tambah"):
                                produk_id = get_produk_id_by_nama(makanan)
                                if produk_id:
                                    add_transaksi(user_id, produk_id, formatted_tanggal, jumlah, total_harga, is_paid=False)
                                    st.success("Berhasil ditambahkan")
                                else:
                                    st.error("Produk tidak ditemukan di database.")
                            
                    # List belanjaan
                    st.subheader("🛍️ Keranjang")
                    st.info('Berikut adalah list yang belum Anda bayar. Jika sudah membayar mohon klik terbayarkan pada item.')
                    with st.container(border=True):
                        data = get_user_transaksi(st.session_state.username)
                        if data:
                            header_cols = st.columns([3, 3, 2, 2, 6])
                            header_cols[0].write("Tanggal")
                            header_cols[1].write("Produk")
                            header_cols[2].write("Jumlah")
                            header_cols[3].write("Harga")
                            header_cols[4].write("Aksi")
                            for row in data:
                                col2, col3, col4, col5, col6 = st.columns([3, 3, 2, 2, 6])
                                col2.write(row['tanggal'])
                                col3.write(row['produk'])
                                formatted_jumlah = f"{row['jumlah']}" #as str
                                col4.write(formatted_jumlah)
                                formatted_total_harga = f"Rp {row['total_harga']:,.0f}" #as str
                                col5.write(formatted_total_harga)

                                if "show_confirmation" not in st.session_state:
                                    st.session_state.show_confirmation = False
                                if "trigger_rerun" not in st.session_state:
                                    st.session_state.trigger_rerun = False
                                @st.dialog("Konfirmasi Penghapusan")
                                def dialog_hapus_item(row):
                                    if "delete_success" not in st.session_state:
                                        st.session_state["delete_success"] = False 

                                    if not st.session_state["delete_success"]:
                                        st.write(f"Apakah Anda yakin ingin menghapus item: **{row['produk']}**?")
                                        col_confirm, col_cancel = st.columns([1, 1])

                                        with col_confirm:
                                            if st.button("Ya, Hapus", key=f"confirm_delete_{row['belanjaan_id']}"):
                                                delete_transaksi(row['belanjaan_id'])
                                                st.session_state["delete_success"] = True
                                                st.session_state["refresh_key"] += 1 

                                        with col_cancel:
                                            if st.button("Batal", key=f"cancel_delete_{row['belanjaan_id']}"):
                                                st.stop()

                                    if st.session_state["delete_success"]:
                                        st.success("Item berhasil dihapus.")
                                        st.stop()
                                
                                if "refresh_key" not in st.session_state:
                                    st.session_state["refresh_key"] = 0

                                with col6:
                                    col6_1, col6_2 = st.columns([3,3])
                                    with col6_1:
                                        if st.button("❌ Hapus", key=f"delete_{row['belanjaan_id']}"):
                                            dialog_hapus_item(row)
                                    with col6_2:
                                        if st.button("✅ Terbayar", key=f"paid_{row['belanjaan_id']}"):
                                            terbayarkan(row['belanjaan_id'])
                                            st.session_state["refresh_key"] += 1
                                #popup
                                if st.session_state.show_confirmation:
                                    st.warning("Apakah Anda yakin ingin menghapus item ini?")
                                    
                                    col_confirm, col_cancel = st.columns([1, 1])
                                    with col_confirm:
                                        if st.button("Ya, Hapus", key=f"confirm_delete_{row['belanjaan_id']}"):
                                            # Panggil fungsi penghapusan
                                            delete_transaksi(row['belanjaan_id'])
                                            st.success("Belanjaan berhasil dihapus.")
                                            #st.session_state.show_confirmation = False  
                                            st.session_state["show_confirmation"] = False
                                            st.rerun()
                                            
                                    with col_cancel:
                                        if st.button("Batal", key=f"cancel_delete_{row['belanjaan_id']}"):
                                            #st.session_state.show_confirmation = False
                                            st.session_state["show_confirmation"] = False
                                            st.rerun()
                                    
                            total = sum([row['total_harga'] for row in data])
                            st.write(f"### Total tanggungan: Rp. {total}")
                        else:
                            st.info("Belum ada data belanjaan.")
                else:
                    st.error("Nama pengguna tidak ditemukan.")
            else:
                st.warning("Masukkan nama Anda untuk memulai belanja.")

        with tab2:
            #berisi history belanja dilihat dari is_paid = 1 dan berdasar dari user_id
            st.subheader("📑 Riwayat")
            st.info('Berikut adalah riwaya belanja Anda')
            with st.container(border=True):
                if st.session_state.username:
                    data = get_riwayat_belanja(st.session_state.username)
                    if data:
                        header_cols = st.columns([3, 3, 2, 2])
                        header_cols[0].write("Tanggal")
                        header_cols[1].write("Produk")
                        header_cols[2].write("Jumlah")
                        header_cols[3].write("Total Harga")
                        for row in data:
                            col2, col3, col4, col5 = st.columns([3, 3, 2, 2])
                            col2.write(row['tanggal'])
                            col3.write(row['produk'])
                            formatted_jumlah = f"{row['jumlah']}" #as str
                            col4.write(formatted_jumlah)
                            formatted_total_harga = f"Rp {row['total_harga']:,.0f}" #as str
                            col5.write(formatted_total_harga)
                        total = sum([row['total_harga'] for row in data])
                        #st.write(f"Total Riwayat Belanja: Rp {total}")
                    else:
                        st.info("Belum ada riwayat belanja.")
                else:
                    st.warning("Masukkan nama Anda untuk melihat riwayat belanja.")
    
    else:
        st.warning("Masukkan username dan password.")
else:
    st.write("")

with tab3:
    # Tampilkan harga makanan
    st.subheader("🍩 Daftar harga")
    st.info("Berikut adalah daftar harga jajanan dan minuman yang ada di Indrimart.")
    df_harga_makanan = pd.DataFrame(list(harga_makanan.items()), columns=["Makanan & Minuman", "Harga & Gambar"])
    df_harga_makanan["Harga"] = df_harga_makanan["Harga & Gambar"].apply(lambda x: f"Rp. {int(x[0]):,.0f}")
    df_harga_makanan = df_harga_makanan.drop(columns=["Harga & Gambar"])
    st.table(df_harga_makanan)
    st.subheader("💳 Pembayaran")
    st.info("Berikut dimana Anda bisa membayarkan jajanan yang dibeli.")
    
    st.write("BCA - 0840882420 a.n. LAY LI NIE")
    st.write("atau")
    st.image("QR.jpg")
