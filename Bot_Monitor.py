import streamlit as st
import gspread
import gspread.utils
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from streamlit.runtime.scriptrunner import rerun

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="🎫 Bot Fare Monitoring", layout="wide")

# --- STEP 1: เชื่อมต่อ Google Sheets ---
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

# --- STEP 2: โหลดข้อมูลจาก Google Sheet ---
sheet_key = st.secrets["GOOGLE_SHEETS"]["google_sheet_key"]
sh = gc.open_by_key(sheet_key)
worksheet = sh.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- STEP 3: ตรวจสอบว่ามี column 'Check' หรือยัง
if "Check" not in df.columns:
    df["Check"] = ""

# --- STEP 4: กรองเฉพาะแถวที่ยังไม่ตรวจสอบ
df_unchecked = df[df["Check"].isna() | (df["Check"] == "")].copy()
df_unchecked.reset_index(inplace=True)  # เก็บ index เดิมไว้ใช้หาแถวใน Sheet

# --- STEP 5: สร้าง dropdown
dropdown_options = ["✅ Correct", "❌ Not Correct"]

st.title("📋 ตรวจสอบข้อมูลที่ยังไม่ถูกตรวจ")

if df_unchecked.empty:
    st.success("🎉 ข้อมูลทั้งหมดถูกตรวจสอบเรียบร้อยแล้ว!")
else:
    for i, row in df_unchecked.iterrows():
        col1, col2 = st.columns([6, 2])
        with col1:
            st.markdown(f"""
                **PNR:** `{row['PNR']}`  
                **Fare:** {row.get('Fare Amount (THB)', '')}  
                **Working:** {row.get('Working', '')}
            """)
        with col2:
            choice = st.selectbox(
                "เลือกผลตรวจสอบ",
                dropdown_options,
                key=f"dropdown_{i}"
            )
            if choice:
                # หาตำแหน่งใน Google Sheet
                sheet_row_index = row["index"] + 2  # +2 เพราะ header แถวที่ 1
                check_col_index = df.columns.get_loc("Check") + 1  # +1 เพราะ index เริ่มที่ 0

                # แปลงเป็น A1 notation เช่น C5
                cell_range = gspread.utils.rowcol_to_a1(sheet_row_index, check_col_index)

                # อัปเดตแบบปลอดภัย
                worksheet.update(cell_range, [[choice]])

                st.success(f"✅ บันทึกผลให้ {row['PNR']} เรียบร้อยแล้ว")
                rerun()  # รีเฟรชหน้าเพื่อซ่อนรายการนั้น
