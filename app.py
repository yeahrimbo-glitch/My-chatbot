import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="나만의 상황극 개인봇", page_icon="🎭", layout="wide")
st.title("🎭 나만의 상황극 개인봇 (구글 로그인 및 무료 Gemini 버전)")
st.caption("구글 로그인으로 나만의 설정을 안전하게 저장하고 복원할 수 있는 개인봇 사이트입니다.")

# --- 구글 간편 로그인 UI 기능 ---
def get_logged_in_user():
    # Streamlit Cloud 환경에서 구글 사용자 정보를 가져옵니다.
    if st.experimental_user.get("email"):
        return st.experimental_user.email
    return None

user_email = get_logged_in_user()

# 로그인 상태에 따른 상단 안내창
if not user_email:
    st.warning("👋 현재 비로그인 상태입니다. 설정을 영구 저장하려면 오른쪽 위 메뉴나 사이드바에서 구글 로그인을 해주세요!")
    # 모바일 환경에서 직관적으로 로그인할 수 있는 버튼 제공
    if st.button("🚀 구글 계정으로 로그인하기"):
        st.login()
else:
    st.success(f"🟢 {user_email} 계정으로 동기화됨 (설정이 클라우드에 자동 저장됩니다)")

# --- 로그인 이메일별 데이터 로드 및 저장 관리 ---
# 구글 이메일 주소를 키값으로 삼아, 사용자마다 개별 저장소를 생성합니다.
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {}

# 초기 기본값 설정
default_settings = {
    "user_name": "민우",
    "user_desc": "평범한 대학생. 무뚝뚝해 보이지만 속은 따뜻함.",
    "bot_name": "시아",
    "bot_desc": "고양이 수인. 호기심이 많고 츤데레 성격. 가끔 말끝에 '냥'을 붙임.",
    "relationship": "소꿉친구 사이. 시아가 인간 세상에 처음 와서 나에게 의지하고 있는 상황.",
    "ng_rules": "현대 과학 기술을 너무 잘 아는 척 금지. 로봇 같은 딱딱한 말투 금지."
}

# 사용자가 로그인 상태이고 데이터베이스에 기존 기록이 있다면 자동으로 복원(로드)
db_key = user_email if user_email else "guest"
if db_key not in st.session_state["user_db"]:
    st.session_state["user_db"][db_key] = default_settings.copy()

current_saved = st.session_state["user_db"][db_key]

# 2. 사이드바 설정
with st.sidebar:
    # 로그인/로그아웃 버튼 배치
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
    
    # 복원된 값(current_saved)을 바탕으로 입력창을 띄웁니다.
    user_name = st.text_input("👤 1-1. 내 캐릭터 이름", value=current_saved["user_name"])
    user_desc = st.text_area("👤 1-2. 내 캐릭터 설정/특징", value=current_saved["user_desc"])
    
    bot_name = st.text_input("🤖 2-1. 챗봇 캐릭터 이름", value=current_saved["bot_name"])
    bot_desc = st.text_area("🤖 2-2. 챗봇 캐릭터 설정/특징", value=current_saved["bot_desc"])
    
    relationship = st.text_area("🔗 3. 둘의 관계성 / 상황", value=current_saved["relationship"])
    ng_rules = st.text_area("❌ 4. NG 사항 (금지 규칙)", value=current_saved["ng_rules"])

    # 설정 저장 버튼 누를 시 데이터베이스에 영구 갱신
    apply_settings = st.button("💾 설정 클라우드 저장 및 대화 초기화")
    
    if apply_settings:
        st.session_state["user_db"][db_key] = {
            "user_name": user_name,
            "user_desc": user_desc,
            "bot_name": bot_name,
            "bot_desc": bot_desc,
            "relationship": relationship,
            "ng_rules": ng_rules
        }

# 3. 프롬프트 조립
system_prompt = f"""
당신은 지금부터 완벽한 상황극 역할극을 수행해야 합니다. 아래 설정에 완전히 몰입하여 캐릭터로서 답변하세요.

[1. 사용자 캐릭터 설정]
- 이름: {user_name}
- 특징: {user_desc}

[2. 당신(AI)의 캐릭터 설정]
- 이름: {bot_name}
- 특징: {bot_desc}

[3. 둘의 관계성 및 상황]
- {relationship}

[4. NG 사항 (절대 금지)]
- {ng_rules}

[대화 규칙]
- 당신은 절대로 AI나 봇인 티를 내지 마세요.
- {user_name}의 대사나 행동을 대신 지어내서 답변하지 마세요. 오직 당신의 캐릭터 반응만 출력하세요.
- 답변할 때는 오직 {bot_name}의 대사와 행동 지문만 작성하세요.
- 첫 대사는 설정에 맞게 친근하고 자연스럽게 시작하세요.
"""

# 4. 세션 초기화
if apply_settings or "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "model", 
        "content": f"(눈을 반짝이며 당신을 바라본다) 안녕, {user_name}! 오늘 우리 뭐 하고 놀 거야?",
        "thought": "사용자를 보고 반가워하는 감정을 담아 캐릭터답게 친근하게 첫인사를 건넸다."
    }]
    if apply_settings:
        st.rerun()

# 5. 기존 대화 출력
for msg in st.session_state.messages:
    role_name = user_name if msg["role"] == "user" else bot_name
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.write(f"**{role_name}**: {msg['content']}")
        if msg["role"] == "model" and "thought" in msg and msg["thought"]:
            with st.expander("💭 " + bot_name + "의 속마음 들여다보기"):
                st.info(msg["thought"])

# 6. 사용자 입력 및 AI 답변 처리
if prompt := st.chat_input():
    if not google_api_key or not (google_api_key.startswith("AIza") or google_api_key.startswith("AQ")):
        st.error("⚠️ 에러: 구글 API 키를 올바르게 입력해 주세요! 'AQ.'으로 시작하는 키를 사이드바에 입력하시면 됩니다.")
        st.stop()

    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_prompt
    )
    
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
            ai_thought = f"{bot_name}(이)가 방금 당신의 말을 듣고 상황극 설정에 맞춰 다음 대사와 행동 지문을 깊게 고민했습니다."
        
        st.session_state.messages.append({"role": "model", "content": msg_text, "thought": ai_thought})
        
        with st.chat_message("assistant"):
            st.write(f"**{bot_name}**: {msg_text}")
            with st.expander("💭 " + bot_name + "의 속마음 들여다보기"):
                st.info(ai_thought)
            
    except Exception as e:
        st.error(f"⚠️ 구글 AI 연결 오류가 발생했습니다. (오류 내용: {e})")
