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

# ✨ CSS for logo + background
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(92,42,157,0.3), rgba(92,42,157,0.3)),
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

    if (username_input and password_input and not login_btn) or login_btn:
        if username_input == USERNAME and password_input == PASSWORD:
            st.session_state.logged_in = True
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.markdown("""
                <div style="background-color: #ffe6e6; 
                            padding: 16px; 
                            border-radius: 8px; 
                            border: 1px solid #ff4d4d; 
                            color: #990000; 
                            font-size: 14px; 
                            font-weight: bold;
                            display: flex;
                            align-items: center;">
                    <span style="font-size: 22px; margin-right: 10px;">❌</span> 
                    Invalid username or password
                </div>
            """, unsafe_allow_html=True)
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

# ========= ✏️ CHECK PNR =========
selected_columns = [
    "PNR", "RT", "RTF", "RTG", "TQT",
    "Fare Amount THB (2C2P)", "GRAND TOTAL (Amadeus)", "Working", "Comment"
]
available_columns = [col for col in selected_columns if col in df.columns]
df_selected = df[available_columns].copy()

if "Check" not in df.columns:
    df["Check"] = ""
df_selected["Check"] = df["Check"]

df_selected = df_selected[df_selected["Check"] == ""].reset_index(drop=True)

# ====== ⛱ FILTER SECTION ======
working_options = df_selected["Working"].dropna().unique().tolist()
selected_working = st.sidebar.multiselect("📌 Filter by Working", options=working_options, default=working_options)
df_selected = df_selected[df_selected["Working"].isin(selected_working)]

search_pnr = st.sidebar.text_input("🔍 Search by PNR")
if search_pnr:
    df_selected = df_selected[df_selected["PNR"].str.contains(search_pnr, case=False, na=False)]

if df_selected.empty:
    st.success("✅ All cases have been checked!")
    st.stop()

# Move 'Comment' column to end
if "Comment" in df_selected.columns:
    cols = [col for col in df_selected.columns if col != "Comment"] + ["Comment"]
    df_selected = df_selected[cols]

# ========= 📝 DATA EDITOR =========
dropdown_options = ["✅ Correct", "❌ Not Correct"]

st.title("✨ Bot Check working cases")
edited_df = st.data_editor(
    df_selected,
    column_config={
        "Check": st.column_config.SelectboxColumn(
            "Check",
            help="Select whether the case is Correct or Not Correct",
            options=dropdown_options,
            required=False
        )
    },
    use_container_width=True,
    num_rows="dynamic"
)

# ========= ✅ SUBMIT =========
if st.button("📂 Submit Result"):
    sheet_data = worksheet.get_all_records()
    df_full = pd.DataFrame(sheet_data)

    for idx, row in edited_df.iterrows():
        pnr = row["PNR"]
        check_value = row["Check"]
        df_full.loc[df_full["PNR"] == pnr, "Check"] = check_value

    worksheet.clear()
    worksheet.update([df_full.columns.values.tolist()] + df_full.values.tolist())

    st.markdown("""
        <div style="background-color: #d4edda;
                    color: #155724;
                    padding: 16px;
                    border-radius: 8px;
                    border: 2px solid #c3e6cb;
                    font-size: 14px;
                    font-weight: bold;
                    box-shadow: 0 0 10px rgba(21,87,36,0.3);
                    margin-bottom: 14px;
                    text-align: center;">
            ✅ Submission successful!
        </div>
    """, unsafe_allow_html=True)
