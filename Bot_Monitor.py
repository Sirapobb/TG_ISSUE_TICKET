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

# STEP 2: โหลดข้อมูล
sheet_key = st.secrets["GOOGLE_SHEETS"]["google_sheet_key"]
sh = gc.open_by_key(sheet_key)
worksheet = sh.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# STEP 3: เลือกคอลัมน์ที่ต้องการ
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

# STEP 4: เพิ่มคอลัมน์ "ตรวจสอบ"
df_selected["ตรวจสอบ"] = ""  # ค่าว่างเริ่มต้น

# STEP 5: แสดง title
st.title("🎫 ข้อมูลการจองตั๋ว (Bot Monitoring)")

# STEP 6: CSS สำหรับ wrap ข้อความในตาราง
st.markdown("""
    <style>
        .stDataFrame div {
            white-space: pre-wrap !important;
            text-align: left !important;
            line-height: 1.2em;
        }
        .stDataFrame td {
            vertical-align: top;
        }
    </style>
""", unsafe_allow_html=True)

# STEP 7: แสดง dropdown ต่อแถว
options = ["✅ Correct", "❌ Not Correct"]
selected_statuses = []

st.markdown("## ✏️ ตรวจสอบแต่ละรายการ")
for idx, row in df_selected.iterrows():
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown(f"**PNR:** `{row['PNR']}` | **Fare:** {row['Fare Amount (THB)']} | **Working:** {row['Working']}")
    with col2:
        status = st.selectbox("เลือกสถานะ", options, key=f"status_{idx}")
        selected_statuses.append(status)

# STEP 8: บันทึกผลตรวจสอบใน DataFrame
df_selected["ตรวจสอบ"] = selected_statuses

# STEP 9: แสดง DataFrame สุดท้าย
st.markdown("## 🧾 สรุปรายการพร้อมสถานะตรวจสอบ")
st.dataframe(df_selected, use_container_width=True)
