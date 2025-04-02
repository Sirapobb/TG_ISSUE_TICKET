import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# ตั้งค่าหน้าเว็บ
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

# STEP 3: เลือกเฉพาะคอลัมน์ที่ต้องการแสดง
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
df_selected = df[available_columns]

# STEP 4: CSS สำหรับให้ข้อความ wrap + ยืดความสูงแถวอัตโนมัติ
st.markdown("""
    <style>
        /* Wrap text inside DataFrame cells */
        .stDataFrame div {
            white-space: pre-wrap !important;
            text-align: left !important;
            line-height: 1.2em;
        }
        /* Optional: force top alignment */
        .stDataFrame td {
            vertical-align: top;
        }
    </style>
""", unsafe_allow_html=True)

# STEP 5: แสดงผล
st.title("🎫 ข้อมูลการจองตั๋ว (Bot Monitoring)")
st.dataframe(df_selected, use_container_width=True)
