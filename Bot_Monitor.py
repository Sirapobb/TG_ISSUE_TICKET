import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="🎫 Bot Fare Monitoring", layout="wide")

# ============ LOGIN WITH SIDEBAR ============
# --- Simple login ---
st.sidebar.title("🔐 Login")
USERNAME = st.secrets["GOOGLE_SHEETS"]["username"]
PASSWORD = st.secrets["GOOGLE_SHEETS"]["password"]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    username_input = st.sidebar.text_input("Username")
    password_input = st.sidebar.text_input("Password", type="password")
    login_btn = st.sidebar.button("Login")

    if login_btn:
        if username_input == USERNAME and password_input == PASSWORD:
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()  # rerun after successful login
        else:
            st.error("❌ Invalid username or password")
    st.stop()  # stop further execution if not logged in
# ============================================

# STEP 1: เชื่อม Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
credentials_dict = {
    "type": st.secrets["GOOGLE_SHEETS"]["type"],
    "project_id": st.secrets["GOOGLE_SHEETS"]["project_id"],
    "private_key_id": st.secrets["GOOGLE_SHEETS"]["private_key_id"],
    "private_key": st.secrets["GOOGLE_SHEETS"]["private_key"],
    "client_email": st.secrets["GOOGLE_SHEETS"]["client_email"],
    "client_id": st.secrets["GOOGLE_SHEETS"]["client_id"],
    "auth_uri": st.secrets["GOOGLE_SHEETS"]["auth_uri"],
    "token_uri": st.secrets["GOOGLE_SHEETS"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["GOOGLE_SHEETS"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["GOOGLE_SHEETS"]["client_x509_cert_url"]
}
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
gc = gspread.authorize(credentials)

# STEP 2: โหลดข้อมูลจาก Google Sheet
sheet_key = st.secrets["GOOGLE_SHEETS"]["google_sheet_key"]
sh = gc.open_by_key(sheet_key)
worksheet = sh.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# STEP 3: เลือกเฉพาะคอลัมน์ที่ต้องการ
selected_columns = [
    "PNR",
    "RT",
    "RTF",
    "RTG",
    "TQT",
    "Fare Amount (THB)",
    "GRAND_TOTAL_CLEAN",
    "Working"
]
available_columns = [col for col in selected_columns if col in df.columns]
df_selected = df[available_columns].copy()

# STEP 4: เพิ่มคอลัมน์ "ตรวจสอบ" ถ้ายังไม่มี
if "ตรวจสอบ" not in df.columns:
    df["ตรวจสอบ"] = ""

# นำค่าจากต้นฉบับมาใส่ใน df_selected ด้วย
if "ตรวจสอบ" in df.columns:
    df_selected["ตรวจสอบ"] = df["ตรวจสอบ"]
else:
    df_selected["ตรวจสอบ"] = ""

# STEP 4.5: กรองเฉพาะรายการที่ยังไม่ตรวจสอบ
df_selected = df_selected[df_selected["ตรวจสอบ"] == ""].reset_index(drop=True)

# ถ้าไม่มีรายการให้ตรวจสอบ
if df_selected.empty:
    st.success("✅ ทุกเคสได้รับการตรวจสอบแล้ว!")
    st.stop()

# STEP 5: กำหนดค่าที่สามารถเลือกได้
dropdown_options = ["✅ Correct", "❌ Not Correct"]

# STEP 6: ใช้ st.data_editor พร้อม dropdown
st.title("🎫 ตรวจสอบข้อมูลและบันทึกผล")
edited_df = st.data_editor(
    df_selected,
    column_config={
        "ตรวจสอบ": st.column_config.SelectboxColumn(
            "ตรวจสอบ",
            help="เลือกสถานะว่า Correct หรือ Not Correct",
            options=dropdown_options,
            required=False
        )
    },
    use_container_width=True,
    num_rows="dynamic"
)

# STEP 7: ปุ่มบันทึกกลับเข้า Google Sheet
if st.button("💾 บันทึกผลตรวจสอบกลับเข้า Google Sheet"):
    # โหลดข้อมูลใหม่ทั้งหมดจาก sheet
    sheet_data = worksheet.get_all_records()
    df_full = pd.DataFrame(sheet_data)

    # ใส่ค่าผลตรวจสอบเฉพาะแถวที่ตรงกัน (ใช้ PNR)
    for idx, row in edited_df.iterrows():
        pnr = row["PNR"]
        check_value = row["ตรวจสอบ"]
        df_full.loc[df_full["PNR"] == pnr, "ตรวจสอบ"] = check_value

    # เขียนทับ Google Sheet (clear ก่อน)
    worksheet.clear()
    worksheet.update([df_full.columns.values.tolist()] + df_full.values.tolist())

    st.success("✅ บันทึกสำเร็จเรียบร้อยแล้ว!")
