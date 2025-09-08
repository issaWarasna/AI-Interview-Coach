# Importing necessary libraries
import streamlit as st
import google.generativeai as genai
from streamlit_js_eval import streamlit_js_eval

# Configure Gemini API using Streamlit secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Streamlit page configuration
st.set_page_config(page_title="Streamlit Chat", page_icon="💬")
st.title("AI Interview Coach")


# ---------- Setup Stage ----------
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

# Helper functions to update session state
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True
    
if not st.session_state.setup_complete:
    st.subheader('Personal information', divider='rainbow')

    st.session_state["name"] = st.text_input("Name", value=st.session_state.get("name", ""))
    st.session_state["experience"] = st.text_area("Experience", value=st.session_state.get("experience", ""))
    st.session_state["skills"] = st.text_area("Skills", value=st.session_state.get("skills", ""))

    st.subheader('Company and Position', divider='rainbow')

    st.session_state["level"] = st.radio("Choose level", ["Junior", "Mid-level", "Senior"], index=0)
    st.session_state["position"] = st.selectbox("Choose a position", ["Data Scientist", "Data engineer", "ML Engineer", "AI Engineer", "BI Analyst", "Financial Analyst"])
    st.session_state["company"] = st.selectbox("Choose a Company", ["Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify"])


    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")


# ---------- Interview Stage ----------
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:
    st.info("Start by introducing yourself.", icon="👋")

    # Initialize messages ONCE with a strong prompt - NOW this condition will work!
    if "messages" not in st.session_state:
        intro_prompt = (
            f"You are Sarah Johnson, an HR executive at {st.session_state['company']} interviewing {st.session_state['name']} "
            f"who has experience: {st.session_state['experience']} "
            f"and skills: {st.session_state['skills']}. "
            f"You are conducting a professional interview for the role of {st.session_state['level']} {st.session_state['position']} "
            f"at {st.session_state['company']}. "
            f"Introduce yourself professionally with your name and role, then ask relevant behavioral questions. "
            f"Keep the interview professional, engaging, and appropriate for the position level. "
            f"Do not use placeholder text like '[Your Name]' - you are Sarah Johnson."
        )
        st.session_state.messages = [{"role": "assistant", "content": intro_prompt, "hidden": True}]

    # Initialize Gemini chat session if not already
    if "chat" not in st.session_state:
        st.session_state.chat = genai.GenerativeModel("gemini-2.0-flash-exp").start_chat(
            history=[{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages]
        )

    # Display previous chat messages (skip hidden ones)
    for message in st.session_state.messages:
        if not message.get("hidden", False):  # Only show non-hidden messages
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer.", max_chars=1000):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Assistant's streamed response
            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = st.session_state.chat.send_message(prompt, stream=True)
                    response_text = st.write_stream(part.text for part in stream)

                # Save assistant response
                st.session_state.messages.append({"role": "assistant", "content": response_text})

            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True


# ---------- Feedback Trigger Stage ----------
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")


# ---------- Feedback Stage ----------
if st.session_state.feedback_shown:
    st.subheader("Feedback")

    # Prepare conversation history (excluding hidden messages)
    conversation_history = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in st.session_state.messages 
        if not msg.get("hidden", False)
    ])

    # Create feedback prompt
    feedback_prompt = f"""You are a helpful tool that provides feedback on an interviewee performance.
Before the Feedback give a score of 1 to 10.
Follow this format:
Overall Score: //Your score
Feedback: //Here you put your feedback
Give only the feedback do not ask any additional questions.

This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any conversation: 

{conversation_history}"""

    # Generate feedback using Gemini
    feedback_model = genai.GenerativeModel("gemini-2.0-flash-exp")
    feedback_response = feedback_model.generate_content(feedback_prompt)
    
    st.write(feedback_response.text)

    # Button to restart the interview
    if st.button("Restart Interview", type="primary"):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")