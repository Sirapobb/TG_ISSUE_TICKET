import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="🎫 Bot Fare Monitoring", layout="wide")

# --- STEP 1: เชื่อม Google Sheets ---
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

# --- STEP 2: โหลดข้อมูล ---
sheet_key = st.secrets["GOOGLE_SHEETS"]["google_sheet_key"]
sh = gc.open_by_key(sheet_key)
worksheet = sh.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- STEP 3: เลือกเฉพาะคอลัมน์ที่ต้องการ ---
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

# --- STEP 4: แสดงผลแบบ Responsive HTML Table ---
st.title("🎫 ข้อมูลการจองตั๋ว (Bot Monitoring)")

table_html = df_selected.to_html(classes='styled-table', index=False, escape=False)

table_css = """
<style>
    .table-container {
        overflow-x: auto;
        max-width: 100%;
    }
    .styled-table {
        border-collapse: collapse;
        width: 100%;
        table-layout: fixed;
        font-size: 14px;
        min-width: 1200px;
    }
    .styled-table thead tr {
        background-color: #f0f2f6;
        text-align: left;
    }
    .styled-table th, .styled-table td {
        border: 1px solid #ddd;
        padding: 8px;
        white-space: pre-wrap;
        word-wrap: break-word;
        vertical-align: top;
    }
    /* ปรับความกว้างเฉพาะคอลัมน์ที่ยาว */
    .styled-table th:nth-child(2),
    .styled-table td:nth-child(2),
    .styled-table th:nth-child(3),
    .styled-table td:nth-child(3),
    .styled-table th:nth-child(4),
    .styled-table td:nth-child(4),
    .styled-table th:nth-child(5),
    .styled-table td:nth-child(5) {
        width: 300px;
    }
</style>
"""

st.markdown(table_css + f'<div class="table-container">{table_html}</div>', unsafe_allow_html=True)
