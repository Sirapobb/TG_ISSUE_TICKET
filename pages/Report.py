import streamlit as st
import pandas as pd
import gspread
from datetime import timedelta
from io import BytesIO
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title="Bot Performance Report",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Simple login ---
st.sidebar.title("🔐 Login")
USERNAME = "TG_ISSUE_TICKET"
PASSWORD = "TRUETOUCH"

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

st.markdown("### Bot Performance Report (New Project)")

# --- Google Sheets auth ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_dict = {
    "type": st.secrets["GOOGLE_SHEETS"]["type"],
    "project_id": st.secrets["GOOGLE_SHEETS"]["project_id"],
    "private_key_id": st.secrets["GOOGLE_SHEETS"]["private_key_id"],
    "private_key": st.secrets["GOOGLE_SHEETS"]["private_key"].replace("\\n", "\n"),
    "client_email": st.secrets["GOOGLE_SHEETS"]["client_email"],
    "client_id": st.secrets["GOOGLE_SHEETS"]["client_id"],
    "auth_uri": st.secrets["GOOGLE_SHEETS"]["auth_uri"],
    "token_uri": st.secrets["GOOGLE_SHEETS"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["GOOGLE_SHEETS"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["GOOGLE_SHEETS"]["client_x509_cert_url"]
}
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
gc = gspread.authorize(credentials)

# --- Read ALL_PNR sheet ---
sh = gc.open_by_key(st.secrets["GOOGLE_SHEETS"]["google_sheet_key"])
sheet = sh.worksheet("ALL_PNR")
data = sheet.get_all_records()
df = pd.DataFrame(data)

# --- Process ---
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y').dt.date

# --- Sidebar filter ---
unique_dates = sorted(df['Date'].unique())
start_date = st.sidebar.date_input(
    "Start Date",
    value=max(unique_dates),
    min_value=min(unique_dates),
    max_value=max(unique_dates)
)
end_date = st.sidebar.date_input(
    "End Date",
    value=max(unique_dates),
    min_value=min(unique_dates),
    max_value=max(unique_dates)
)
if start_date > end_date:
    st.sidebar.error("Start Date must be before or equal to End Date.")

# --- Filter dataframe ---
filtered_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

# --- Summary stats ---
summary = filtered_df.groupby('Date').agg(
    Total_Case=('PNR', 'count'),
    Bot_Working_Case=('Done', lambda x: (x == "Yes").sum())
).reset_index()
summary['% Bot Working'] = summary.apply(
    lambda row: f"{(row['Bot_Working_Case'] / row['Total_Case'] * 100):.2f}" if row['Total_Case'] > 0 else "0.00",
    axis=1
)

# --- Add total row ---
total_row = summary[['Total_Case', 'Bot_Working_Case']].sum()
total_row['Date'] = 'Total'
total_row['% Bot Working'] = f"{(total_row['Bot_Working_Case'] / total_row['Total_Case'] * 100):.2f}" if total_row['Total_Case'] > 0 else "0.00"
summary = pd.concat([summary, pd.DataFrame([total_row])], ignore_index=True)

# --- Show summary in UI ---
st.write("### Summary")
st.dataframe(summary)

# --- Excel export ---
def create_excel(summary, filtered_df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        summary.to_excel(writer, index=False, sheet_name="Summary")
        filtered_df.to_excel(writer, index=False, sheet_name="Detail")
    output.seek(0)
    return output

excel_data = create_excel(summary, filtered_df)
st.download_button(
    label="📄 Download Report",
    data=excel_data,
    file_name="Bot_Performance_Report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.write("### Detail")
st.dataframe(filtered_df)
