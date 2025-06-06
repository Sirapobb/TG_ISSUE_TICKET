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
notification_sheet = sh.worksheet("NOTIFICATION")
notification_data = notification_sheet.get_all_records()
df_notification = pd.DataFrame(notification_data)

# Fetch data from "Logdata" sheet
logdata_sheet = sh.worksheet("LOG_DATA")
logdata_data = logdata_sheet.get_all_records()
df_logdata = pd.DataFrame(logdata_data)

# def set_reason(row):
#     if row['RPA_Delete'] == 'No':
#         return 'ไม่เข้าเงื่อนไขที่ Bot ทำงาน ให้ Supervisor ตรวจสอบ'
#     elif row['RPA_Delete'] == 'Yes':
#         if row['RPA_SendSMS'] == 'No':
#             return 'Bot ทำการลบรายการใน e-service แล้ว แต่ยังไม่ได้ดำเนินการในขั้นตอนส่ง SMS และ VOC'
#         elif row['RPA_SendSMS'] == 'Yes':
#             return 'Bot ทำการลบรายการและส่ง sms เรียบร้อย เหลือขั้นตอน SendVOC ที่ยังไม่ได้ดำเนินการ'
#     return ''

# def highlight_time(s,start):
#     return ['background-color: rgb(234, 226, 73); color: #000000;' if s['RPA_Starttime'] == start else '' for _ in s]

def display_card(title, value):
    html = f"""
    <div style="
        background-color: #F0F2F6;
        border-radius: 10px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        padding: 15px;
        text-align: center;
        margin: 10px;
    ">
        <p style='font-size: 20px; font-weight: bold; color: #000000; margin: 0;'>{title}</p>
        <p style='font-size: 30px; font-weight: bold; margin: 0; color: #a933dc;'>{value}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# Display the latest notification
if not df_notification.empty:
    last_record = df_notification.iloc[-1]  # Get the last row of the Notification DataFrame
    notification = last_record.get('NOTIFICATION', 'No notification available')  # Replace 'Notification' with the actual column name
    startdate = last_record.get('RPA_STARTDATE')
    starttime = last_record.get('RPA_STARTTIME')

    total_bot_cases = len(df_logdata[(df_logdata['RPA_Result'] == 'Yes') & (df_logdata['RPA_Startdate'] == startdate)])
    display_card("Today Bot Working Cases", total_bot_cases)
    #display_card("จำนวน Case ที่ Bot ทำงานในวันนี้", total_bot_cases)
    # Display the notification
    st.markdown("------------------------")
    #st.markdown("##### 📢 การแจ้งเตือนล่าสุด")
    st.markdown("#### 📢 Notification Lastest")
    st.markdown(f"```\n{notification}\n```")
    st.markdown("------------------------")
    # Filter Logdata for relevant entries
    if not df_logdata.empty:
        relevant_logs = df_logdata[['PNR','Date','Time','Check BKKTG0','Check SRC','Check HK', 'Check SSR UNMR',
                                               'Check THAI-AMEX','Check 217','Check PC','Working', 'Done']]
        relevant_logs = relevant_logs[(relevant_logs['Done'] == 'No')] # & (relevant_logs['Date'] == startdate)]
        
        #relevant_logs['Reason'] =  relevant_logs.apply(set_reason, axis=1)
        relevant_logs = relevant_logs[['PNR','Date','Time','Check BKKTG0','Check SRC','Check HK', 'Check SSR UNMR',
                                               'Check THAI-AMEX','Check 217','Check PC','Working', 'Done']]
        if not relevant_logs.empty:
            relevant_logs = relevant_logs.reset_index(drop=True)
            relevant_logs = relevant_logs[::-1] 
            styled_logs = relevant_logs.style.apply(highlight_time, axis=1, args=(starttime,))
            st.markdown("#### ⚠️ Case Detail for Supervisor Checking")
            st.dataframe(styled_logs) 
        else:
            st.info("Bot ทำงานสำเร็จทุกเคสในรอบเวลานี้ ไม่มีรายการคงเหลือ")
else:
    st.warning("No data available in the Notification sheet.")
