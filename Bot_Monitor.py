import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="🎫 Bot Fare Monitoring", layout="wide")

# STEP 1: เชื่อมต่อ Google Sheets
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

# STEP 2: โหลดข้อมูลทั้งหมด
sheet_key = st.secrets["GOOGLE_SHEETS"]["google_sheet_key"]
sh = gc.open_by_key(sheet_key)
worksheet = sh.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# STEP 3: ถ้ายังไม่มีคอลัมน์ "ตรวจสอบ" ให้เพิ่ม
if "ตรวจสอบ" not in df.columns:
    df["ตรวจสอบ"] = ""

# STEP 4: กรองเฉพาะแถวที่ยังไม่ถูกตรวจสอบ
df_unchecked = df[df["ตรวจสอบ"].isna() | (df["ตรวจสอบ"] == "")].copy()
df_unchecked.reset_index(inplace=True)  # เก็บ index เดิมไว้ใช้ระบุแถวใน Google Sheet

# STEP 5: ตัวเลือก dropdown
dropdown_options = ["✅ Correct", "❌ Not Correct"]

st.title("📋 ตรวจสอบข้อมูลที่ยังไม่ถูกตรวจ")

if df_unchecked.empty:
    st.success("🎉 ข้อมูลทั้งหมดถูกตรวจสอบเรียบร้อยแล้ว!")
else:
    for i, row in df_unchecked.iterrows():
        col1, col2 = st.columns([6, 2])
        with col1:
            st.markdown(f"**PNR:** `{row['PNR']}` | **Fare:** {row['Fare Amount (THB)']} | **Working:** {row['Working']}")
        with col2:
            choice = st.selectbox(
                "เลือกผลตรวจสอบ",
                dropdown_options,
                key=f"dropdown_{i}"
            )
            if choice:
                # ตำแหน่งใน Google Sheet จริง (ต้อง +2 เพราะ header คือแถวที่ 1 และ index เริ่มที่ 0)
                sheet_row_index = row["index"] + 2
                worksheet.update_cell(sheet_row_index, df.columns.get_loc("ตรวจสอบ") + 1, choice)
                st.success(f"✅ บันทึกผลให้ {row['PNR']} เรียบร้อยแล้ว")
                st.experimental_rerun()  # Refresh เพื่อแสดงเฉพาะแถวที่ยังไม่ถูกตรวจใหม่
