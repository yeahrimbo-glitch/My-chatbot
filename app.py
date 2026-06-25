import streamlit as st
import google.generativeai as genai
import json
import os

st.set_page_config(
    page_title="나만의 상황극 개인봇", 
    page_icon="🎭", 
    layout="wide"
)

st.title("🎭 나만의 상황극 개인봇 (무료 버전)")
st.caption("비용 걱정 없이 내 설정대로 마음껏 대화할 수 있는 곳입니다.")

# --- 서버 영구 저장용 JSON 데이터베이스 기능 ---
DB_FILE = "user_settings_db.json"

def load_persisted_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_to_persisted_db(email_key, data):
    db = load_persisted_db()
    db[email_key] = data
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
    except:
        pass

default_settings = {
    "user_name": "이단",
    "user_desc": "평범한 대학생. 무뚝뚝해 보이지만 속은 따뜻함.",
    "bot_name": "Phil Coulson",
    "bot_desc": "S.H.I.E.L.D. 요원. 침착하고 신뢰할 수 있는 성격.",
    "relationship": "요원과 보호 대상자 사이.",
    "ng_rules": "현대 과학 기술 너무 잘 아는 척 금지."
}

db_key = "guest"
persisted_db = load_persisted_db()

if db_key not in persisted_db:
    persisted_db[db_key] = default_settings.copy()

current_saved = persisted_db[db_key]

# --- 사이드바 설정 영역 ---
with st.sidebar:
    st.markdown("---")
    google_api_key = st.text_input(
        "Google Gemini API Key", 
        key="chatbot_api_key", 
        type="password"
    )
    st.markdown("---")
    st.subheader("⚙️ 상황극 세부 설정")
    
    user_name = st.text_input(
        "👤 1-1. 내 캐릭터 이름", 
        value=current_saved["user_name"]
    )
    user_desc = st.text_area(
        "👤 1-2. 내 설정/특징", 
        value=current_saved["user_desc"]
    )
    
    st.markdown("---")
    st.markdown("**🤖 2. 챗봇 캐릭터 설정**")
    
    # [짤림 방지] 안전하게 여러 줄로 나눈 파일 업로드 코드
    uploaded_file = st.file_uploader(
        "🤖 챗봇 프로필 사진 업로드", 
        type=["png", "jpg", "jpeg"]
    )
    
    if uploaded_file:
        bot_avatar = uploaded_file.getvalue()
        st.image(bot_avatar, width=100, caption="업로드 완료!")
    else:
        bot_avatar = "🤖"
        
    bot_name = st.text_input(
        "🤖 2-1. 챗봇 이름", 
        value=current_saved["bot_name"]
    )
    bot_desc = st.text_area(
        "🤖 2-2. 챗봇 설정/특징", 
        value=current_saved["bot_desc"]
    )
    relationship = st.text_area(
        "🔗 3. 둘의 관계성 / 상황", 
        value=current_saved["relationship"]
    )
    ng_rules = st.text_area(
        "❌ 4. NG 사항 (금지 규칙)", 
        value=current_saved["ng_rules"]
    )

    apply_settings = st.button("💾 설정 저장 및 대화 초기화")
    
    if apply_settings:
        new_data = {
            "user_name": user_name,
            "user_desc": user_desc,
            "bot_name": bot_name,
            "bot_desc": bot_desc,
            "relationship": relationship,
            "ng_rules": ng_rules
        }
        save_to_persisted_db(db_key, new_data)
        st.toast("⚙️ 설정이 안전하게 자동 저장되었습니다!")
        
        # [짤림 방지] 세로 정렬
        st.session_state["messages"] = [
            {
                "role": "model", 
                "content": f"준비됐네, {user_name}. 어떤 이야기를 시작해볼까?", 
                "thought": "사용자의 설정을 확인하고 인사를 건넸다."
            }
        ]
        st.rerun()

# --- 상황극 프롬프트 조립 ---
system_prompt = f"""
당신은 완벽한 상황극 역할극을 수행해야 합니다.
[1. 사용자 설정] 이름: {user_name} / 특징: {user_desc}
[2. 당신(AI)의 설정] 이름: {bot_name} / 특징: {bot_desc}
[3. 관계성] {relationship}
[4. NG 사항] {ng_rules}

[대화 규칙]
- AI인 티를 내지 말고 {bot_name}의 대사와 지문만 작성하세요.
- {user_name}의 대사를 대신 지어내지 마세요.
"""

# --- 대화 방 초기화 ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "model", 
            "content": f"준비됐네, {user_name}. 어떤 이야기를 시작해볼까?", 
            "thought": "사용자의 설정을 확인하고 인사를 건넸다."
        }
    ]

for msg in st.session_state.messages:
    role_name = user_name if msg["role"] == "user" else bot_name
    avatar_to_use = None if msg["role"] == "user" else bot_avatar
    
    with st.chat_message(
        "user" if msg["role"] == "user" else "assistant", 
        avatar=avatar_to_use
    ):
        st.write(f"**{role_name}**: {msg['content']}")
        if msg["role"] == "model" and msg.get("thought"):
            with st.expander("💭 속마음 들여다보기"):
                st.info(msg["thought"])

# --- 유저 입력 및 답변 처리 ---
if prompt := st.chat_input():
    if not google_api_key or not (google_api_key.startswith("AIza") or google_api_key.startswith("AQ")):
        st.error("⚠️ 에러: 구글 API 키를 사이드바에 입력해 주세요!")
        st.stop()

    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction=system_prompt
    )
    
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )
    
    history = []
    for msg in st.session_state.messages[:-1]:
        history.append({"role": msg["role"], "parts": [msg["content"]]})
        
    try:
        chat = model.start_chat(history=history)
        config = genai.types.GenerationConfig(
            thinking_config={"thinking_budget": 1024}
        )
        response = chat.send_message(
            prompt, 
            generation_config=config
        )
        
        msg_text = response.text
        ai_thought = ""
        try:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'thought') and part.thought:
                    ai_thought = part.text
                    break
        except:
            pass
            
        if not ai_thought:
            ai_thought = "심도 있게 고심했습니다."
        
        st.session_state.messages.append(
            {
                "role": "model", 
                "content": msg_text, 
                "thought": ai_thought
            }
        )
        st.rerun()
            
    except Exception as e:
        st.error(f"⚠️ 구글 AI 연결 오류 발생: {e}")
