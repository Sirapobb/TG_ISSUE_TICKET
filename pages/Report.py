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

st.markdown("### Bot Performance Report (Summary and Detail)")

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

# --- Process date ---
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y', errors='coerce').dt.date
unique_dates = df['Date'].dropna().unique()

if len(unique_dates) > 0:
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

    # --- Summary by Date ---
    summary_by_date = filtered_df.groupby('Date').agg(
        Total_Case=('PNR', 'count'),
        Bot_Working_Case=('Done', lambda x: (x == 'Yes').sum())
    ).reset_index()
    summary_by_date['Supervisor_Working_Case'] = summary_by_date['Total_Case'] - summary_by_date['Bot_Working_Case']
    summary_by_date['% Bot Working'] = summary_by_date.apply(
        lambda row: f"{(row['Bot_Working_Case'] / row['Total_Case'] * 100):.2f}" if row['Total_Case'] > 0 else "0.00",
        axis=1
    )

    # --- Add total row ---
    total_row = summary_by_date[['Total_Case', 'Bot_Working_Case', 'Supervisor_Working_Case']].sum()
    total_row['Date'] = 'Total'
    total_row['% Bot Working'] = f"{(total_row['Bot_Working_Case'] / total_row['Total_Case'] * 100):.2f}" if total_row['Total_Case'] > 0 else "0.00"
    summary_by_date = pd.concat([summary_by_date, pd.DataFrame([total_row])], ignore_index=True)

    st.write("### Summary by Date")
    st.dataframe(summary_by_date)

    # --- Summary by 15-minute interval ---
    full_intervals = pd.date_range("00:00", "23:59", freq="15T").strftime('%H:%M').tolist()
    summary_all_dates = pd.DataFrame()

    for date in pd.date_range(start=start_date, end=end_date).date:
        df_date = filtered_df[filtered_df['Date'] == date].copy()
        if df_date.empty:
            continue
        df_date['Time_dt'] = pd.to_datetime(df_date['Time'], format='%H:%M:%S', errors='coerce')
        df_date = df_date.dropna(subset=['Time_dt'])
        df_date['15_minute_interval'] = df_date['Time_dt'].dt.floor('15T').dt.strftime('%H:%M')

        grouped = df_date.groupby('15_minute_interval').agg(
            Total=('PNR', 'count'),
            Bot_Working=('Done', lambda x: (x == 'Yes').sum())
        ).reset_index()
        grouped['Supervisor_Working'] = grouped['Total'] - grouped['Bot_Working']
        grouped['% Bot Working'] = grouped.apply(
            lambda row: f"{(row['Bot_Working'] / row['Total'] * 100):.2f}" if row['Total'] > 0 else "0.00",
            axis=1
        )
        grouped['Date'] = date

        complete_intervals = pd.DataFrame({'15_minute_interval': full_intervals})
        complete = complete_intervals.merge(grouped, on='15_minute_interval', how='left').fillna(0)
        complete['Date'] = date
        complete['Total'] = complete['Total'].astype(int)
        complete['Bot_Working'] = complete['Bot_Working'].astype(int)
        complete['Supervisor_Working'] = complete['Supervisor_Working'].astype(int)

        summary_all_dates = pd.concat([summary_all_dates, complete], ignore_index=True)

    st.write("### Detail: 15-minute intervals for all dates")
    st.dataframe(summary_all_dates)

    # --- Excel export ---
    def create_excel(summary_by_date, summary_all_dates):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            summary_by_date.to_excel(writer, index=False, sheet_name="Summary")
            for date, df_group in summary_all_dates.groupby('Date'):
                sheet_name = pd.to_datetime(date).strftime('%d-%b-%y')
                df_group_out = df_group.copy()
                df_group_out['Date'] = pd.to_datetime(df_group_out['Date']).dt.strftime('%d-%b-%y')
                df_group_out.rename(columns={
                    '15_minute_interval': '15 Minute',
                    'Total': 'Total Case',
                    'Bot_Working': 'Bot Working Case',
                    'Supervisor_Working': 'Supervisor Working Case'
                }, inplace=True)
                df_group_out = df_group_out[['Date', '15 Minute', 'Total Case', 'Bot Working Case', 'Supervisor Working Case', '% Bot Working']]
                df_group_out.to_excel(writer, index=False, sheet_name=sheet_name)

            summary_all_dates.to_excel(writer, index=False, sheet_name="All Detail")
        output.seek(0)
        return output

    excel_data = create_excel(summary_by_date, summary_all_dates)
    st.download_button(
        label="📄 Download Excel Report",
        data=excel_data,
        file_name="Bot_Performance_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("No valid dates found in your data. Please check date format in Google Sheet.")
