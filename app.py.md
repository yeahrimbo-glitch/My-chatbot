# app.py  
import streamlit as st  
from openai import OpenAI  
  
# 1. 웹사이트 타이틀 및 설정  
st.set_page_config(page_title="나만의 개인봇", page_icon="🤖")  
st.title("🤖 나만의 비밀 개인봇")  
st.caption("🚀 언제든 대화할 수 있는 나만의 AI 친구입니다.")  
  
# 2. API 키 입력 (보안을 위해 사이드바에 배치)  
with st.sidebar:  
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")  
    "[OpenAI API 키 발급받기](https://platform.openai.com/api-keys)"  
      
    # 내 봇의 페르소나(성격) 설정하기  
    system_instruction = st.text_area(  
        "봇의 성격/규칙 정하기",  
        value="당신은 사용자의 다정하고 위트 있는 개인 비서이자 절친입니다. 짧고 친근하게 반말로 답해주세요."  
    )  
  
# 3. 대화 기록 저장 공간 초기화  
if "messages" not in st.session_state:  
    st.session_state["messages"] = [{"role": "assistant", "content": "안녕! 오늘 무슨 일 있어? 얘기해 봐!"}]  
  
# 4. 기존 대화 화면에 그리기  
for msg in st.session_state.messages:  
    st.chat_message(msg["role"]).write(msg["content"])  
  
# 5. 사용자 입력 처리  
if prompt := st.chat_input():  
    if not openai_api_key:  
        st.info("왼쪽 사이드바에 OpenAI API Key를 입력해야 대화를 시작할 수 있어!")  
        st.stop()  
  
    # 클라이언트 설정 및 사용자 메시지 추가  
    client = OpenAI(api_key=openai_api_key)  
    st.session_state.messages.append({"role": "user", "content": prompt})  
    st.chat_message("user").write(prompt)  
  
    # 시스템 지시어(성격)를 대화 맨 앞에 주입  
    api_messages = [{"role": "system", "content": system_instruction}] + st.session_state.messages  
  
    # OpenAI API 호출 (2026년 기준 가성비 최고인 gpt-4o-mini 사용)  
    response = client.chat.completions.create(  
        model="gpt-4o-mini",   
        messages=api_messages  
    )  
      
    # AI 답변 화면에 출력 및 저장  
    msg = response.choices[0].message.content  
    st.session_state.messages.append({"role": "assistant", "content": msg})  
    st.chat_message("assistant").write(msg)  
