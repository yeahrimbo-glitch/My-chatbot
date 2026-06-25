import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="나만의 상황극 개인봇", page_icon="🎭", layout="wide")
st.title("🎭 나만의 상황극 개인봇 (무료 Gemini 버전)")
st.caption("비용 걱정 없이 마음껏 대화할 수 있는 무료 개인봇 사이트입니다.")

# 1. 사이드바 설정
with st.sidebar:
    google_api_key = st.text_input("Google Gemini API Key", key="chatbot_api_key", type="password")
    st.markdown("[구글 무료 API 키 발급받기](https://aistudio.google.com)")
    st.markdown("---")
    st.subheader("⚙️ 상황극 세부 설정")
    
    # 설정 입력 칸들
    user_name = st.text_input("👤 1-1. 내 캐릭터 이름", value="민우")
    user_desc = st.text_area("👤 1-2. 내 캐릭터 설정/특징", value="평범한 대학생. 무뚝뚝해 보이지만 속은 따뜻함.")
    
    bot_name = st.text_input("🤖 2-1. 챗봇 캐릭터 이름", value="시아")
    bot_desc = st.text_area("🤖 2-2. 챗봇 캐릭터 설정/특징", value="고양이 수인. 호기심이 많고 츤데레 성격. 가끔 말끝에 '냥'을 붙임.")
    
    relationship = st.text_area("🔗 3. 둘의 관계성 / 상황", value="소꿉친구 사이. 시아가 인간 세상에 처음 와서 나에게 의지하고 있는 상황.")
    ng_rules = st.text_area("❌ 4. NG 사항 (금지 규칙)", value="현대 과학 기술을 너무 잘 아는 척 금지. 로봇 같은 딱딱한 말투 금지.")

    # 설정 저장 및 대화 초기화 버튼
    apply_settings = st.button("🔄 설정 저장 및 대화 초기화")
    
    st.markdown("---")
    st.subheader("💾 설정 백업 및 불러오기")
    
    # [백업 기능 1] 현재 설정을 텍스트 파일로 다운로드하기
    backup_text = f"""[내 캐릭터 이름]
{user_name}

[내 캐릭터 설정]
{user_desc}

[챗봇 캐릭터 이름]
{bot_name}

[챗봇 캐릭터 설정]
{bot_desc}

[관계성 및 상황]
{relationship}

[NG 사항]
{ng_rules}"""

    st.download_button(
        label="📥 현재 설정 백업 파일 다운로드",
        data=backup_text,
        file_name=f"backup_{bot_name}_settings.txt",
        mime="text/plain"
    )
    
    st.caption("💡 팁: 다운로드한 텍스트 파일의 내용을 복사해서 나중에 언제든 이 설정창에 다시 붙여넣으시면 됩니다!")

# 2. 프롬프트 조립 (★ 속마음을 생각하도록 지시 추가)
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

[대화 규칙 - 중요]
- 당신은 절대로 AI나 봇인 티를 내지 마세요.
- {user_name}의 대사나 행동을 대신 지어내서 답변하지 마세요. 오직 당신의 캐릭터 반응만 출력하세요.
- 답변할 때는 오직 {bot_name}의 대사와 행동 지문만 작성하세요. (예: "(부끄러운 듯 고개를 숙이며) ...바보, 그런 거 아냐.")
- 첫 대사는 설정에 맞게 친근하고 자연스럽게 시작하세요.
"""

# 3. 세션 초기화
if apply_settings or "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "model", 
        "content": f"(눈을 반짝이며 당신을 바라본다) 안녕, {user_name}! 오늘 우리 뭐 하고 놀 거야?",
        "thought": "사용자를 보고 반가워하는 감정을 담아 고양이 수인답게 친근하게 첫인사를 건넸다."
    }]
    if apply_settings:
        st.rerun()

# 4. 기존 대화 출력 (★ 속마음도 보이게 UI 디자인)
for msg in st.session_state.messages:
    role_name = user_name if msg["role"] == "user" else bot_name
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.write(f"**{role_name}**: {msg['content']}")
        # 봇의 답변이고 속마음 데이터가 존재한다면 접이식 메뉴로 노출
        if msg["role"] == "model" and "thought" in msg and msg["thought"]:
            with st.expander("💭 " + bot_name + "의 속마음 들여다보기"):
                st.info(msg["thought"])

# 5. 사용자 입력 및 AI 답변 처리
if prompt := st.chat_input():
    if not google_api_key or not (google_api_key.startswith("AIza") or google_api_key.startswith("AQ")):
        st.error("⚠️ 에러: 구글 API 키를 올바르게 입력해 주세요! 'AQ.'으로 시작하는 키를 사이드바에 입력하시면 됩니다.")
        st.stop()

    genai.configure(api_key=google_api_key)
    
    # 최신 gemini-2.5-flash 모델 적용
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_prompt
    )
    
    # 유저 메시지 저장 및 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(f"**{user_name}**: {prompt}")

    # 과거 대화 기록 정렬
    history = []
    for msg in st.session_state.messages[:-1]:
        history.append({"role": msg["role"], "parts": [msg["content"]]})
    
    try:
        chat = model.start_chat(history=history)
        
        # 구글에 보낼 요청 내용 설정 변경 (대답과 생각을 함께 추론하도록 유도)
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
                # 내부 구조에서 생각 메타데이터가 있으면 가져옴
                if hasattr(part, 'thought') and part.thought:
                    ai_thought = part.text
                    break
        except:
            pass
            
        if not ai_thought:
            ai_thought = f"{bot_name}(이)가 방금 당신의 말('{prompt}')을 듣고 상황극 설정에 맞춰 다음 대사와 행동 지문을 깊게 고민했습니다."
        
        # 대화 기록에 저장
        st.session_state.messages.append({"role": "model", "content": msg_text, "thought": ai_thought})
        
        # 화면에 출력
        with st.chat_message("assistant"):
            st.write(f"**{bot_name}**: {msg_text}")
            with st.expander("💭 " + bot_name + "의 속마음 들여다보기"):
                st.info(ai_thought)
            
    except Exception as e:
        st.error(f"⚠️ 구글 AI 연결 오류가 발생했습니다. (오류 내용: {e})")
