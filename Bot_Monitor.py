import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="🎫 Bot Fare Monitoring", layout="wide")

# --- STEP 1: เชื่อมต่อกับ Google Sheets ---
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
worksheet = sh.sheet1  # หรือ sh.worksheet("ชื่อชีต")
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- STEP 3: เลือกเฉพาะคอลัมน์ที่ต้องการแสดง ---
selected_columns = [
    "PNR",
    "EP Number",
    "Approval Code",
    "Fare Amount (THB)",
    "Expiry Date",
    "RT",
    "RTF",
    "RTG",
    "TQT"
]
# ตรวจสอบว่าคอลัมน์มีอยู่จริงใน DataFrame
available_columns = [col for col in selected_columns if col in df.columns]
df_selected = df[available_columns]

# --- STEP 4: แสดงผลบน Streamlit พร้อม wrap ข้อความ ---
st.title("🎫 ข้อมูลการจองตั๋ว (Bot Monitoring)")

# CSS เพื่อให้ข้อความใน cell ตัดบรรทัด (wrap text)
wrap_css = """
    <style>
    .dataframe td {
        white-space: normal !important;
        word-break: break-word !important;
        text-align: left !important;
    }
    .stDataFrame div[data-testid="stMarkdownContainer"] {
        white-space: normal;
    }
    </style>
"""
st.markdown(wrap_css, unsafe_allow_html=True)

# แสดง DataFrame
st.dataframe(df_selected, use_container_width=True)
