import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from streamlit.runtime.scriptrunner import rerun

# Set page config
st.set_page_config(page_title="🎫 Bot Fare Monitoring", layout="wide")

# --- Step 1: Connect to Google Sheets ---
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

# --- Step 2: Load Google Sheet Data ---
sheet_key = st.secrets["GOOGLE_SHEETS"]["google_sheet_key"]
sh = gc.open_by_key(sheet_key)
worksheet = sh.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- Step 3: Ensure "Check" column exists ---
if "Check" not in df.columns:
    df["Check"] = ""

# --- Step 4: Filter rows where Check is blank ---
df_unchecked = df[df["Check"].isna() | (df["Check"] == "")].copy()
df_unchecked.reset_index(inplace=True)  # preserve original index for Sheet row reference

# --- Step 5: Dropdown options ---
dropdown_options = ["✅ Correct", "❌ Not Correct"]

# --- Step 6: Display unchecked items ---
st.title("📋 Check Unverified PNR Records")

if df_unchecked.empty:
    st.success("🎉 All records have been checked!")
else:
    for i, row in df_unchecked.iterrows():
        col1, col2 = st.columns([6, 2])
        with col1:
            st.markdown(
                f"""
                **PNR:** `{row['PNR']}`  
                **Fare:** {row.get('Fare Amount (THB)', '')}  
                **Working:** {row.get('Working', '')}
                """
            )
        with col2:
            choice = st.selectbox(
                "Select status",
                dropdown_options,
                key=f"dropdown_{i}"
            )
            if choice:
                # Get actual row in Sheet: +2 because of header row (1-based indexing)
                sheet_row_index = row["index"] + 2
                check_col_index = df.columns.get_loc("Check") + 1
                worksheet.update_cell(sheet_row_index, check_col_index, choice)
                st.success(f"✅ Updated {row['PNR']} as: {choice}")
                rerun()  # reload view to hide checked record
