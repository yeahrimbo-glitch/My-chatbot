import streamlit as st
import google.generativeai as genai
import json
import os

st.set_page_config(page_title="나만의 상황극 개인봇", page_icon="🎭", layout="wide")
st.title("🎭 나만의 상황극 개인봇 (구글 로그인 및 무료 Gemini 버전)")
st.caption("구글 로그인으로 나만의 설정을 안전하게 저장하고 복원할 수 있는 개인봇 사이트입니다.")

# --- 📁 [NEW] 서버 영구 저장용 JSON 데이터베이스 기능 ---
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

# --- 🔒 [FIX] 구글 간편 로그인 에러 수정 ---
def get_logged_in_user():
    # AttributeError 해결: .get() 대신 정석적인 attribute(.email) 접근법 사용
    try:
        if hasattr(st, "user") and st.user.email:
            return st.user.email
    except:
        pass
    try:
        if hasattr(st, "experimental_user") and st.experimental_user.email:
            return st.experimental_user.email
    except:
        pass
    return None

user_email = get_logged_in_user()

# 로그인 상태 안내 UI
if not user_email:
    st.warning("👋 현재 비로그인 상태입니다. 다른 기기에서도 설정을 복원하려면 구글 로그인을 해주세요!")
    if st.button("🚀 구글 계정으로 로그인하기"):
        st.login()
else:
    st.success(f"🟢 {user_email} 계정으로 동기화됨 (설정이 클라우드 전용 파일에 영구 저장됩니다)")

# --- 🔄 로그인 계정별 기존 설정 자동 복원 ---
default_settings = {
    "user_name": "이단",
    "user_desc": "평범한 대학생. 무뚝뚝해 보이지만 속은 따뜻함.",
    "bot_name": "Phil Coulson",
    "bot_desc": "S.H.I.E.L.D. 요원. 침착하고 신뢰할 수 있는 성격.",
    "relationship": "요원과 보호 대상자 사이.",
    "ng_rules": "현대 과학 기술을 너무 잘 아는 척 금지. 로봇 같은 말투 금지."
}

# 영구 저장된 파일 데이터베이스에서 내 이메일 설정 찾아오기
db_key = user_email if user_email else "guest"
persisted_db = load_persisted_db()

if db_key not in persisted_db:
    persisted_db[db_key] = default_settings.copy()

current_saved = persisted_db[db_key]

# --- ⚙️ 사이드바 설정 영역 ---
with st.sidebar:
    if user_email:
        if st.button("🔒 로그아웃"):
            st.logout()
            st.rerun()
    else:
        if st.button("🔓 구글 로그인"):
            st.login()
            st.rerun()
            
    st.markdown("---")
    google_api_key = st.text_input("Google Gemini API Key", key="chatbot_api_key", type="password")
    st.markdown("[구글 무료 API 키 발급받기](https://aistudio.google.com)")
    st.markdown("---")
    st.subheader("⚙️ 상황극 세부 설정")
    
    # 불러온 값으로 입력창 채우기
    user_name = st.text_input("👤 1-1. 내 캐릭터 이름", value=current_saved["user_name"])
    user_desc = st.text_area("👤 1-2. 내 캐릭터 설정/특징", value=current_saved["user_desc"])
    bot_name = st.text_input("🤖 2-1. 챗봇 캐릭터 이름", value=current_saved["bot_name"])
    bot_desc = st.text_area("🤖 2-2. 챗봇 캐릭터 설정/특징", value=current_saved["bot_desc"])
    relationship = st.text_area("🔗 3. 둘의 관계성 / 상황", value=current_saved["relationship"])
    ng_rules = st.text_area("❌ 4. NG 사항 (금지 규칙)", value=current_saved["ng_rules"])

    # 설정 저장 버튼 누를 때 파일(DB)에 영구 저장
    apply_settings = st.button("💾 설정 클라우드 저장 및 대화 초기화")
    
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
        st.toast("⚙️ 설정이 안전하게 저장되었습니다!")

    st.markdown("---")
    st.subheader("💾 설정 파일로 백업")
    backup_text = f"내이름: {user_name}\n내설정: {user_desc}\n봇이름: {bot_name}\n봇설정: {bot_desc}\n관계: {relationship}\nNG: {ng_rules}"
    st.download_button(
        label="📥 텍스트 파일로 내보내기",
        data=backup_text,
        file_name=f"backup_{bot_name}.txt",
        mime="text/plain"
    )

# --- 🎭 상황극 프롬프트 조립 ---
system_prompt = f"""
당신은 지금부터 완벽한 상황극 역할극을 수행해야 합니다. 아래 설정에 완전히 몰입하여 캐릭터로서 답변하세요.
[1. 사용자 캐릭터 설정] 이름: {user_name} / 특징: {user_desc}
[2. 당신(AI)의 캐릭터 설정] 이름: {bot_name} / 특징: {bot_desc}
[3. 관계성 및 상황] {relationship}
[4. NG 사항] {ng_rules}

[대화 규칙]
- AI인 티를 내지 말고 오직 {bot_name}의 대사와 행동 지문만 작성하세요.
- {user_name}의 대사나 행동을 대신 지어내지 마세요.
"""

# --- 💬 대화 방 초기화 및 출력 ---
if apply_settings or "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "model", 
        "content": f"(당신을 바라보며 지긋이 고개를 끄덕인다) 준비됐네, {user_name}. 어떤 이야기를 시작해볼까?",
        "thought": "사용자의 로그인 상태 및 설정을 확인하고 안정감 있는 요원의 톤으로 첫 인사를 건넸다."
    }]
    if apply_settings:
        st.rerun()

for msg in st.session_state.messages:
    role_name = user_name if msg["role"] == "user" else bot_name
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.write(f"**{role_name}**: {msg['content']}")
        if msg["role"] == "model" and "thought" in msg and msg["thought"]:
            with st.expander("💭 " + bot_name + "의 속마음 들여다보기"):
                st.info(msg["thought"])

# --- 🚀 유저 입력 및 답변 처리 ---
if prompt := st.chat_input():
    if not google_api_key or not (google_api_key.startswith("AIza") or google_api_key.startswith("AQ")):
        st.error("⚠️ 에러: 구글 API 키를 사이드바에 입력해 주세요!")
        st.stop()

    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(f"**{user_name}**: {prompt}")

    history = []
    for msg in st.session_state.messages[:-1]:
        history.append({"role": msg["role"], "parts": [msg["content"]]})
    
    try:
        chat = model.start_chat(history=history)
        config = genai.types.GenerationConfig(thinking_config={"thinking_budget": 1024})
        response = chat.send_message(prompt, generation_config=config)
        
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
            ai_thought = f"{bot_name}(이)가 설정을 기반으로 대사와 지문을 심도 있게 고심했습니다."
        
        st.session_state.messages.append({"role": "model", "content": msg_text, "thought": ai_thought})
        
        with st.chat_message("assistant"):
            st.write(f"**{bot_name}**: {msg_text}")
            with st.expander("💭 " + bot_name + "의 속마음 들여다보기"):
                st.info(ai_thought)
            
    except Exception as e:
        st.error(f"⚠️ 구글 AI 연결 오류가 발생했습니다. (오류 내용: {e})")
