import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(
    page_title="Bot Monitoring",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ใช้ Secrets โดยตรงจาก Streamlit
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
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
}  # ไม่ต้องใช้ json.loads
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
gc = gspread.authorize(credentials)
#sh = gc.open_by_key('--- google sheet key ---')
sh = gc.open_by_key(st.secrets["GOOGLE_SHEETS"]["google_sheet_key"])
notification_sheet = sh.worksheet("Notification")
notification_data = notification_sheet.get_all_records()
df_notification = pd.DataFrame(notification_data)

# Fetch data from "Logdata" sheet
logdata_sheet = sh.worksheet("Logdata")
logdata_data = logdata_sheet.get_all_records()
df_logdata = pd.DataFrame(logdata_data)
