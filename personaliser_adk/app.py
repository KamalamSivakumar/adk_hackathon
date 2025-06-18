import os
import asyncio
import streamlit as st
from dotenv import load_dotenv

from agent import root_agent 
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("❌ GOOGLE_API_KEY is missing! Please set it in a .env file.")
    st.stop()

# Streamlit page setup
st.set_page_config(page_title="🎮 Task Gamifier", layout="wide")
st.title("📅 Gamify & Schedule Tasks")

# -------------------------------
# 🚪 Exit Button & Session Reset
# -------------------------------
if st.button("🛑 Exit & Restart Session"):
    for key in ["session", "runner", "history"]:
        st.session_state.pop(key, None)
    st.success("✅ Session restarted.")
    st.rerun()

# -------------------------------
# 🧠 Initialize session + runner
# -------------------------------
if "session_service" not in st.session_state:
    st.session_state.session_service = InMemorySessionService()

if "session" not in st.session_state:
    st.session_state.session = asyncio.run(
        st.session_state.session_service.create_session(
            app_name="task_gamifier_app",
            user_id="user-001"
        )
    )

if "runner" not in st.session_state:
    st.session_state.runner = Runner(
        app_name=st.session_state.session.app_name,
        agent=root_agent,
        session_service=st.session_state.session_service
    )

if "history" not in st.session_state:
    st.session_state.history = []

# -------------------------------
# ✍️ Task Input Form
# -------------------------------
with st.form(key="task_form", clear_on_submit=True):
    task_input = st.text_input("📝 What task do you want to gamify & schedule?", key="task_input")
    submitted = st.form_submit_button("🚀 Submit")

if submitted and task_input:
    async def process():
        final_response = None
        async for event in st.session_state.runner.run_async(
            session_id=st.session_state.session.id,
            user_id=st.session_state.session.user_id,
            new_message=Content(role="user", parts=[Part(text=task_input)])
        ):
            if event.is_final_response():
                final_response = event.content.parts[0].text
        return final_response

    try:
        response = asyncio.run(process())
        st.session_state.history.append((task_input, response))
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Error: {e}")

# -------------------------------
# 💬 Chat History
# -------------------------------
st.subheader("💬 Interaction History")
for user_input, agent_response in reversed(st.session_state.history):
    st.markdown(f"**You:** {user_input}")
    st.markdown(f"🤖 **Agent:** {agent_response}")
    st.markdown("---")

# -------------------------------
# 🧹 Clear Chat History
# -------------------------------
if st.button("Clear Chat Only"):
    st.session_state.history = []
    st.rerun()
