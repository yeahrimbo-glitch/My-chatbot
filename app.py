import streamlit as st
import google.generativeai as genai
import json
import os

st.set_page_config(page_title="나만의 상황극 개인봇", page_icon="🎭", layout="wide")
st.title("🎭 나만의 상황극 개인봇 (무료 Gemini 버전)")
st.caption("비용 걱정 없이 내 설정대로 마음껏 대화할 수 있는 무료 개인봇 사이트입니다.")

# --- 📁 서버 영구 저장용 JSON 데이터베이스 기능 ---
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

# --- 🔄 기존 설정 자동 복원 ---
default_settings = {
    "user_name": "이단",
    "user_desc": "평범한 대학생. 무뚝뚝해 보이지만 속은 따뜻함.",
    "bot_name": "Phil Coulson",
    "bot_desc": "S.H.I.E.L.D. 요원. 침착하고 신뢰할 수 있는 성격. 어벤져스 멤버들과 가깝다.",
    "relationship": "요원과 보호 대상자 사이.",
    "ng_rules": "현대 과학 기술을 너무 잘 아는 척 금지. 로봇 같은 말투 금지."
}

db_key = "guest"
persisted_db = load_persisted_db()

if db_key not in persisted_db:
    persisted_db[db_key] = default_settings.copy()

current_saved = persisted_db[db_key]

# --- ⚙️ 사이드바 설정 영역 ---
with st.sidebar:
    st.markdown("---")
    google_api_key = st.text_input("Google Gemini API Key", key="chatbot_api_key", type="password")
    st.markdown("[구글 무료 API 키 발급받기](https://aistudio.google.com)")
    st.markdown("---")
    st.subheader("⚙️ 상황극 세부 설정")
    
    user_name = st.text_input("👤 1-1. 내 캐릭터 이름", value=current_saved["user_name"])
    user_desc = st.text_area("👤 1-2. 내 캐릭터 설정/특징", value=current_saved["user_desc"])
    
    st.markdown("---")
    st.markdown("**🤖 2. 챗봇 캐릭터 설정**")
    
    # 📸 https://nuli.navercorp.com/community/article/1133151
    uploaded_file = st.file_uploader("🤖 챗봇 프로필 사진 업로드 (휴대폰 갤러리에서 선택)", type=["png", "jpg", "jpeg"])
    
    # 사진을 올리면 사이드바에 미리 보여줍니다. 안 올리면 기본 로봇 아이콘이 적용됩니다.
    bot_avatar = uploaded_file if uploaded_file else "🤖"
    if uploaded_file:
        st.image(uploaded_file, width=100, caption="업로드된 프로필 사진")
        
    bot_name = st.text_input("🤖 2-1. 챗봇 캐릭터 이름", value=current_saved["bot_name"])
    bot_desc = st.text_area("🤖 2-2. 챗봇 캐릭터 설정/특징", value=current_saved["bot_desc"])
    
    relationship = st.text_area("🔗 3. 둘의 관계성 / 상황", value=current_saved["relationship"])
    ng_rules = st.text_area("❌ 4. NG 사항 (금지 규칙)", value=current_saved["ng_rules"])

    apply_settings = st.button("💾 설정 저장 및 대화 초기화")
    st.caption("💡 입력창에 텍스트를 적으면 클라우드에 주기적으로 자동 저장됩니다.")
    
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
        st.toast("⚙️ 캐릭터 텍스트 설정이 안전하게 자동 저장되었습니다!")
        
        # 대화 초기화
        st.session_state["messages"] =
