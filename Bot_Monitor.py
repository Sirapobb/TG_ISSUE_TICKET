import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(
    page_title="TG ISSUE TICKET",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✨ ใส่ CSS โลโก้ + background ต่อจากนี้
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(179,157,219),0.3), rgba(179,157,219,0.3),
                    url("https://www.catdumb.com/wp-content/uploads/2021/05/AD-Gineric-Landing-01.jpg");
        background-size: cover;
        background-attachment: fixed;
        background-position: bottom;
    }
    div[data-testid="stDataFrame"] th {
        background-color: #5c2a9d !important;
        color: white !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        text-align: center;
    }
    div[data-testid="stDataFrame"] tbody tr:nth-child(even) {
        background-color: #f3eefc !important;
    }
    div[data-testid="stDataFrame"] tbody tr:nth-child(odd) {
        background-color: #e7dcf5 !important;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(92, 42, 157, 0.1);
        overflow: hidden;
    }
    </style>
""", unsafe_allow_html=True)

# ========= 🔐 LOGIN =========
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
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    st.stop()

# ========= 📊 LOAD GOOGLE SHEET =========
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

sheet_key = st.secrets["GOOGLE_SHEETS"]["google_sheet_key"]
sh = gc.open_by_key(sheet_key)
worksheet = sh.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# ========= ✏️ PNR ตรวจสอบ =========
selected_columns = [
    "PNR", "RT", "RTF", "RTG", "TQT",
    "Fare Amount (THB)", "GRAND_TOTAL_CLEAN", "Working"
]
available_columns = [col for col in selected_columns if col in df.columns]
df_selected = df[available_columns].copy()

if "ตรวจสอบ" not in df.columns:
    df["ตรวจสอบ"] = ""
df_selected["ตรวจสอบ"] = df["ตรวจสอบ"]

df_selected = df_selected[df_selected["ตรวจสอบ"] == ""].reset_index(drop=True)

if df_selected.empty:
    st.success("✅ ทุกเคสได้รับการตรวจสอบแล้ว!")
    st.stop()

dropdown_options = ["✅ Correct", "❌ Not Correct"]

st.title("✏️ ตรวจสอบข้อมูลและบันทึกผล")
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

if st.button("💾 บันทึกผลตรวจสอบกลับเข้า Google Sheet"):
    sheet_data = worksheet.get_all_records()
    df_full = pd.DataFrame(sheet_data)

    for idx, row in edited_df.iterrows():
        pnr = row["PNR"]
        check_value = row["ตรวจสอบ"]
        df_full.loc[df_full["PNR"] == pnr, "ตรวจสอบ"] = check_value

    worksheet.clear()
    worksheet.update([df_full.columns.values.tolist()] + df_full.values.tolist())
    st.success("✅ บันทึกสำเร็จเรียบร้อยแล้ว!")
