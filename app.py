import streamlit as st
from openai import OpenAI

# 1. 페이지 설정
st.set_page_config(page_title="나만의 상황극 개인봇", page_icon="🎭", layout="wide")
st.title("🎭 나만의 상황극 개인봇")
st.caption("내가 정한 설정과 상황 속으로 들어가 AI와 대화해보세요.")

# 2. 사이드바 설정 (API 키 및 기본 설정)
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[OpenAI API 키 발급받기](https://platform.openai.com/api-keys)"
    st.markdown("---")
    st.subheader("⚙️ 상황극 세부 설정")
    
    # [설정 1] 내 캐릭터 설정
    st.markdown("### 👤 1. 내 캐릭터 (사용자)")
    user_name = st.text_input("내 캐릭터 이름", value="민우")
    user_desc = st.text_area("내 캐릭터 설정/특징", value="평범한 대학생. 무뚝뚝해 보이지만 속은 따뜻함.")
    
    # [설정 2] 챗봇 캐릭터 설정
    st.markdown("### 🤖 2. 챗봇 캐릭터")
    bot_name = st.text_input("챗봇 캐릭터 이름", value="시아")
    bot_desc = st.text_area("챗봇 캐릭터 설정/특징", value="고양이 수인. 호기심이 많고 츤데레 성격. 가끔 말끝에 '냥'을 붙임.")
    
    # [설정 3] 관계성 및 상황
    st.markdown("### 🔗 3. 둘의 관계성 / 상황")
    relationship = st.text_area("관계 및 현재 상황", value="소꿉친구 사이. 시아가 인간 세상에 처음 와서 나에게 의지하고 있는 상황.")
    
    # [설정 4] NG 사항
    st.markdown("### ❌ 4. NG 사항 (금지 규칙)")
    ng_rules = st.text_area("하지 말아야 할 행동/말", value="현대 과학 기술을 너무 잘 아는 척 금지. 로봇 같은 딱딱한 말투 금지.")

    # 설정 적용 버튼
    apply_settings = st.button("설정 저장 및 대화 초기화")

# 3. 프롬프트(시스템 지시어) 조립하기
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

# 4. 설정 변경 시 대화 리셋
if apply_settings or "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": f"(눈을 반짝이며 당신을 바라본다) 안녕, {user_name}! 오늘 우리 뭐 하고 놀 거야?"}]

# 5. 기존 대화 출력
for msg in st.session_state.messages:
    # 화면에 표시되는 이름을 설정한 이름으로 변경
    role_name = user_name if msg["role"] == "user" else bot_name
    with st.chat_message(msg["role"]):
        st.write(f"**{role_name}**: {msg['content']}")

# 6. 사용자 입력 및 AI 답변 처리
if prompt := st.chat_input():
    if not openai_api_key:
        st.info("왼쪽 사이드바에 OpenAI API Key를 입력해주세요!")
        st.stop()

    client = OpenAI(api_key=openai_api_key)
    
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(f"**{user_name}**: {prompt}")

    # 시스템 프롬프트와 대화 기록 합치기
    api_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

    # 답변 생성
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=api_messages
    )
    
    # AI 답변 출력 및 저장
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    with st.chat_message("assistant"):
        st.write(f"**{bot_name}**: {msg}")
