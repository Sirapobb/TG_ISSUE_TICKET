import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(
    page_title="Bot Monitoring",
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
logemd = sh.worksheet("LOG_EMD")
logdata_data = logdata_sheet.get_all_records()
logemd_data = logdata_sheet.get_all_records()
df_logdata = pd.DataFrame(logdata_data)
df_emd = pd.DataFrame(logemd_data)

# def set_reason(row):
#     if row['RPA_Delete'] == 'No':
#         return 'ไม่เข้าเงื่อนไขที่ Bot ทำงาน ให้ Supervisor ตรวจสอบ'
#     elif row['RPA_Delete'] == 'Yes':
#         if row['RPA_SendSMS'] == 'No':
#             return 'Bot ทำการลบรายการใน e-service แล้ว แต่ยังไม่ได้ดำเนินการในขั้นตอนส่ง SMS และ VOC'
#         elif row['RPA_SendSMS'] == 'Yes':
#             return 'Bot ทำการลบรายการและส่ง sms เรียบร้อย เหลือขั้นตอน SendVOC ที่ยังไม่ได้ดำเนินการ'
#     return ''

# def set_reason(row):
#     if row['Done'] == 'No' and row['Working'] == 'No':
#         return '⚠️ ไม่เข้าเงื่อนไขในการทำรายการ ⚠️'
#     elif row['Done'] == 'No' and row['Working'] == 'Yes':
#         return '🚨เข้าเงื่อนไขการทำรายการ แต่ทำรายการ ISSUE TICKET ไม่สำเร็จ🚨'
#     elif row['Done'] == 'No' and row['Working'] == 'No' and row['Check 217'] == 'FALSE' and row['Fare Amount THB (2C2P)'] == row['GRAND TOTAL (Amadeus)']:
#         return  '🧾 ดำเนินการ EMD Case 🧾'

def set_reason(row):
    # เคส EMD Case ต้องมาก่อนเพราะเป็น subset ของ (Done=No, Working=No)
    if (row['Done'] == 'No' and row['Working'] == 'No' 
        and row['Check 217'] == 'FALSE' 
        and row['GRAND TOTAL (Amadeus)'] != "-"  # ต้องไม่เป็น "-"
        and row['Fare Amount THB (2C2P)'] != row['GRAND TOTAL (Amadeus)']):
        return '🧾 EMD Case ไม่ถูกดำเนินการ 🧾'
    
    elif row['Done'] == 'No' and row['Working'] == 'No':
        return '⚠️ ไม่เข้าเงื่อนไขในการทำรายการ ⚠️'
    
    elif row['Done'] == 'No' and row['Working'] == 'Yes':
        return '🚨 เข้าเงื่อนไขการทำรายการ แต่ทำรายการ ISSUE TICKET ไม่สำเร็จ 🚨'
    
    return None  # กรณีไม่เข้าเงื่อนไขใด ๆ

# def set_reason_emd(row_emd, row):
#     if row['Done'] == 'Yes' and row['Working'] == 'No':
#         if (row_emd['Done'] == 'No' and row_emd['Working'] == 'TRUE')
#             return '🚨 EMD Case เข้าเงื่อนไขแต่ยังไม่ถูกดำเนินการ เนื่องจาก System Error🚨'
#         else:
#             return '🧾 EMD Case ไม่ถูกดำเนินการ 🧾'
        
def highlight_time(s,start):
     return ['background-color: rgb(234, 226, 73); color: #000000;' if s['Time'] == start else '' for _ in s]

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
    last_record = df_notification.iloc[-2]  # Last record df_notification.iloc[-1
    notification = last_record.get('NOTIFICATION', 'No notification available')  # Replace 'Notification' with the actual column name
    startdate = last_record.get('RPA_STARTDATE')
    starttime = last_record.get('RPA_STARTTIME')

    total_bot_cases = len(df_logdata[(df_logdata['Done'] == 'Yes') & (df_logdata['Date'] == startdate)])
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
                                               'Check THAI-AMEX','Check 217','Check PC', 'Fare Amount THB (2C2P)', 'GRAND TOTAL (Amadeus)', 'Working', 'Done']]
        relevant_logs = relevant_logs[(relevant_logs['Done'] == 'No') & (relevant_logs['Date'] == startdate)]
        
        relevant_logs['Reason'] =  relevant_logs.apply(set_reason, axis=1)
        relevant_logs = relevant_logs[['PNR','Date','Time','Reason','Check BKKTG0','Check SRC','Check HK', 'Check SSR UNMR',
                                               'Check THAI-AMEX','Check 217','Check PC', 'Fare Amount THB (2C2P)', 'GRAND TOTAL (Amadeus)','Working', 'Done']]
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

# st.markdown("------------------------")
# st.markdown("#### ⚠️ EMD Case Detail")
