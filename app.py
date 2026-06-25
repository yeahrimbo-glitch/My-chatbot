import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="나만의 상황극 개인봇", page_icon="🎭", layout="wide")
st.title("🎭 나만의 상황극 개인봇 (무료 Gemini 버전)")
st.caption("비용 걱정 없이 마음껏 대화할 수 있는 무료 개인봇 사이트입니다.")

with st.sidebar:
    google_api_key = st.text_input("Google Gemini API Key", key="chatbot_api_key", type="password")
    st.markdown("[구글 무료 API 키 발급받기](https://aistudio.google.com)")
    st.markdown("---")
    st.subheader("⚙️ 상황극 세부 설정")
    
    st.markdown("### 👤 1. 내 캐릭터 (사용자)")
    user_name = st.text_input("내 캐릭터 이름", value="민우")
    user_desc = st.text_area("내 캐릭터 설정/특징", value="평범한 대학생. 무뚝뚝해 보이지만 속은 따뜻함.")
    
    st.markdown("### 🤖 2. 챗봇 캐릭터")
    bot_name = st.text_input("챗봇 캐릭터 이름", value="시아")
    bot_desc = st.text_area("챗봇 캐릭터 설정/특징", value="고양이 수인. 호기심이 많고 츤데레 성격. 가끔 말끝에 '냥'을 붙임.")
    
    st.markdown("### 🔗 3. 둘의 관계성 / 상황")
    relationship = st.text_area("관계 및 현재 상황", value="소꿉친구 사이. 시아가 인간 세상에 처음 와서 나에게 의지하고 있는 상황.")
    
    st.markdown("### ❌ 4. NG 사항 (금지 규칙)")
    ng_rules = st.text_area("하지 말아야 할 행동/말", value="현대 과학 기술을 너무 잘 아는 척 금지. 로봇 같은 딱딱한 말투 금지.")

    apply_settings = st.button("설정 저장 및 대화 초기화")

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
- 답변할 때는 오직 {bot_name}의 대사와 행동 지문만 작성하세요. (예: "(부끄러운 듯 고개를 숙이며) ...바보, 그런 거 아냐.")
- {user_name}의 대사나 행동을 대신 지어내서 답변하지 마세요. 오직 당신의 캐릭터 반응만 출력하세요.
- 첫 대사는 설정에 맞게 친근하고 자연스럽게 시작하세요.
"""

if apply_settings or "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "model", "content": f"(눈을 반짝이며 당신을 바라본다) 안녕, {user_name}! 오늘 우리 뭐 하고 놀 거야?"}]
    if apply_settings:
        st.rerun()

for msg in st.session_state.messages:
    role_name = user_name if msg["role"] == "user" else bot_name
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.write(f"**{role_name}**: {msg['content']}")

if prompt := st.chat_input():
    # 최신 구글 AQ. 시작 키와 기존 AIza 키 모두 허용하도록 수정
    if not google_api_key or not (google_api_key.startswith("AIza") or google_api_key.startswith("AQ")):
        st.error("⚠️ 에러: 구글 API 키를 올바르게 입력해 주세요! 발급받으신 'AQ.'으로 시작하는 키를 입력하시면 됩니다.")
        st.stop()

    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
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
        response = chat.send_message(prompt)
        
        msg_text = response.text
        st.session_state.messages.append({"role": "model", "content": msg_text})
        with st.chat_message("assistant"):
            st.write(f"**{bot_name}**: {msg_text}")
            
    except Exception as e:
        st.error(f"⚠️ 구글 AI 연결 오류가 발생했습니다. 키를 다시 한번 확인해 주세요! (오류 내용: {e})")
