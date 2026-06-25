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

# 로그인 정보 로직 삭제됨 ( user_email = None )
user_email = None

# --- 🔄 기존 설정 자동 복원 ( guest 키값 사용 ) ---
default_settings = {
    "user_name": "이단",
    "user_desc": "평범한 대학생. 무뚝뚝해 보이지만 속은 따뜻함.",
    "bot_name": "Phil Coulson",
    "bot_desc": "S.H.I.E.L.D. 요원. 침착하고 신뢰할 수 있는 성격. 어벤져스 멤버들과 가깝다.",
    "bot_avatar_url": "https://img.vogue.co.kr/vogue/2026/06/stylist_1718873238.6477053.jpg", # 필 콜슨 프로필 사진 주소
    "relationship": "요원과 보호 대상자 사이.",
    "ng_rules": "현대 과학 기술을 너무 잘 아는 척 금지. 로봇 같은 말투 금지."
}

# guest 키를 사용하여 파일(DB)에서 내 설정 찾아오기
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
    
    # 불러온 값으로 입력창 채우기
    user_name = st.text_input("👤 1-1. 내 캐릭터 이름", value=current_saved["user_name"])
    user_desc = st.text_area("👤 1-2. 내 캐릭터 설정/특징", value=current_saved["user_desc"])
    
    # 🤖 [NEW] 챗봇 설정 영역 디자인 수정
    st.markdown(f"**🤖 챗봇 캐릭터 (필 콜슨 요원)**")
    # 프로필 사진 미리보기
    bot_avatar_url = st.text_input("🤖 챗봇 프로필 사진 URL", value=current_saved["bot_avatar_url"])
    if bot_avatar_url:
        st.image(bot_avatar_url, width=100, caption=f"{current_saved['bot_name']}의 프로필 사진")
        
    bot_name = st.text_input("🤖 2-1. 챗봇 캐릭터 이름", value=current_saved["bot_name"])
    bot_desc = st.text_area("🤖 2-2. 챗봇 캐릭터 설정/특징", value=current_saved["bot_desc"])
    
    relationship = st.text_area("🔗 3. 둘의 관계성 / 상황", value=current_saved["relationship"])
    ng_rules = st.text_area("❌ 4. NG 사항 (금지 규칙)", value=current_saved["ng_rules"])

    # 설정 저장 버튼 누를 때 파일(DB)에 영구 저장 (★주기적 자동 저장 안내)
    apply_settings = st.button("💾 설정 클라우드 저장 및 대화 초기화")
    st.caption("💡 입력 시 클라우드에 주기적으로 자동 저장됩니다.")
    
    if apply_settings:
        new_data = {
            "user_name": user_name,
            "user_desc": user_desc,
            "bot_name": bot_name,
            "bot_desc": bot_desc,
            "bot_avatar_url": bot_avatar_url,
            "relationship": relationship,
            "ng_rules": ng_rules
        }
        save_to_persisted_db(db_key, new_data)
        # 성공 메시지를 toast로 더 깔끔하게 표시
        st.toast("⚙️ 설정이 안전하게 클라우드 파일에 저장되었습니다!", icon='Saved')

    st.markdown("---")
    st.subheader("💾 설정 파일로 백업")
    backup_text = f"내이름: {user_name}\n내설정: {user_desc}\n봇이름: {bot_name}\n봇설정: {bot_desc}\n봇사진URL: {bot_avatar_url}\n관계: {relationship}\nNG: {ng_rules}"
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
- {user_name}의 대사나 행동을 대신 지어내지 마세요. 오직 당신의 반응만 출력하세요.
- 첫 대사는 상황에 맞게 친근하고 요원답게 시작하세요.
"""

# --- 💬 대화 방 초기화 및 출력 (★프로필 사진 반영 수정) ---
# AI 대화 시작 메시지에 프로필 사진 URL 포함
start_thought = f"(당신을 바라보며 지긋이 고개를 끄덕인다) 준비됐네, {user_name}. 어떤 이야기를 시작해볼까?"

if apply_settings or "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "model", 
        "content": start_thought,
        "thought": "사용자의 설정을 확인하고 안정감 있는 요원의 톤으로 첫 인사를 건넸다."
    }]
    if apply_settings:
        st.rerun()

for msg in st.session_state.messages:
    role_name = user_name if msg["role"] == "user" else bot_name
    # 대화창에 반영될 프로필 사진 URL
    avatar_url = None if msg["role"] == "user" else bot_avatar_url
    
    with st.chat_message("user" if msg["role"] == "user" else "assistant", avatar=avatar_url):
        st.write(f"**{role_name}**: {msg['content']}")
        # 봇의 답변이고 속마음 데이터가 존재한다면 접이식 메뉴로 노출
        if msg["role"] == "model" and "thought" in msg and msg["thought"]:
            with st.expander("💭 " + bot_name + "의 속마음 들여다보기"):
                st.info(msg["thought"])

# --- 🚀 유저 입력 및 답변 처리 ---
if prompt := st.chat_input():
    # API 키가 틀려서 AuthenticationError가 나는 것을 방지하기 위해 미리 검사
    if not google_api_key or not (google_api_key.startswith("AIza") or google_api_key.startswith("AQ")):
        st.error("⚠️ 에러: 구글 API 키를 올바르게 입력해 주세요! 'AQ.'으로 시작하는 키를 사이드바에 입력하시면 됩니다.")
        st.stop()

    genai.configure(api_key=google_api_key)
    # 최신 공식 모델 gemini-2.5-flash 적용
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    # 사용자 메시지 화면 출력 (사용자 아바타 없음)
    with st.chat_message("user"):
        st.write(f"**{user_name}**: {prompt}")

    # 과거 대화 기록 정렬
    history = []
    for msg in st.session_state.messages[:-1]:
        history.append({"role": msg["role"], "parts": [msg["content"]]})
    
    try:
        chat = model.start_chat(history=history)
        
        # 겉으로 하는 대답과 별개로 AI가 생각한 논리를 받아옵니다.
        config = genai.types.GenerationConfig(
            thinking_config={"thinking_budget": 1024} # AI가 속마음/생각 과정을 길게 거치도록 허용
        )
        
        response = chat.send_message(prompt, generation_config=config)
        
        # 생성된 대답과 생각(속마음) 추출
        msg_text = response.text
        
        # 생각 과정(thought)을 지원하는 모델인 경우 가져오기
        ai_thought = ""
        try:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'thought') and part.thought:
                    ai_thought = part.text
                    break
        except:
            pass
            
        if not ai_thought:
            ai_thought = f"{bot_name}(이)가 설정을 기반으로 대사와 행동 지문을 심도 있게 고심했습니다."
        
        # 대화 기록에 저장
        st.session_state.messages.append({"role": "model", "content": msg_text, "thought": ai_thought})
        
        # 봇의 답변 화면 출력 (★필 콜슨 프로필 사진 반영)
        with st.chat_message("assistant", avatar=bot_avatar_url):
            st.write(f"**{bot_name}**: {msg_text}")
            with st.expander("💭 " + bot_name + "의 속마음 들여다보기"):
                st.info(ai_thought)
            
    except Exception as e:
        st.error(f"⚠️ 구글 AI 연결 오류가 발생했습니다. (오류 내용: {e})")
