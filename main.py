import os
import base64
import re
import json
import streamlit as st
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


# Gmail API 인증 함수
def authenticate_gmail():
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    # 기존에 인증된 token.json 파일이 있으면 불러옴
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 인증 토큰이 없거나 만료된 경우 새로 인증 진행
    if not creds or creds.expired or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # 인증된 정보를 token.json 파일에 저장
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

# 이메일에서 인증번호 추출 함수
def get_verification_code(service):
    # 이메일 목록 가져오기 ("인증번호"가 제목에 포함된 이메일 검색)
    results = service.users().messages().list(userId='me', q="subject:인증번호").execute()
    messages = results.get('messages', [])

    if not messages:
        st.warning("인증번호가 포함된 이메일을 찾을 수 없습니다.")
        return None

    # 첫 번째 이메일 가져오기
    message = service.users().messages().get(userId='me', id=messages[0]['id']).execute()
    
    # 이메일 본문에서 인증번호 추출
    for part in message['payload']['headers']:
        if part['name'] == 'Subject' and '인증번호' in part['value']:
            for msg_part in message['payload']['parts']:
                if 'body' in msg_part and 'data' in msg_part['body']:
                    data = msg_part['body']['data']
                    decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')  # base64 디코딩
                    verification_code = re.findall(r'\d{6}', decoded_data)  # 6자리 숫자 추출
                    if verification_code:
                        return verification_code[0]
    
    return None

# Streamlit 앱 실행 부분
st.set_page_config(page_title="인증번호 추출기", page_icon="🔑")

st.title("📧 Gmail 인증번호 추출기")
st.markdown("이 앱은 Gmail에서 인증번호를 자동으로 추출합니다.")

if st.button("인증번호 추출"):
    with st.spinner("인증번호를 가져오는 중..."):
        service = authenticate_gmail()
        code = get_verification_code(service)
        
        if code:
            st.success(f"인증번호: {code}")
        else:
            st.warning("인증번호를 찾을 수 없습니다.")
