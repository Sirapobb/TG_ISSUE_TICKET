import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

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

# --- STEP 3: เลือกคอลัมน์ที่ต้องการแสดง ---
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

# --- STEP 4: สร้าง CSS และแสดงแบบ HTML เพื่อให้ข้อความตัดบรรทัดได้จริง ---
st.title("🎫 ข้อมูลการจองตั๋ว (Bot Monitoring)")

table_html = df_selected.to_html(classes='styled-table', index=False, escape=False)

# CSS สำหรับ wrap และตกแต่งตาราง
table_css = """
<style>
    .styled-table {
        border-collapse: collapse;
        width: 100%;
        table-layout: fixed;
        font-size: 14px;
    }
    .styled-table thead tr {
        background-color: #f0f2f6;
        text-align: left;
    }
    .styled-table th, .styled-table td {
        border: 1px solid #ddd;
        padding: 8px;
        word-wrap: break-word;
        white-space: pre-wrap;
    }
</style>
"""

# แสดงผล
st.markdown(table_css + table_html, unsafe_allow_html=True)
