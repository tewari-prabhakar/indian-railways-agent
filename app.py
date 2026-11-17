import streamlit as st
from datetime import date
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
from tools import get_trains_between_stations

# 1. Load environment variables (.env)
load_dotenv()

# 2. Configure the browser page
st.set_page_config(page_title="Indian Railways AI Agent", page_icon="🚆")
st.title("🚆 Indian Railways AI Agent")
st.caption("Ask in plain English — e.g., 'What trains run from Ghaziabad to Lucknow tomorrow?'")

MODELS = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash"]

today_str = date.today().strftime("%Y-%m-%d")
system_instruction = f"""
You are a helpful Indian Railways Train Inquiry Assistant. Today's date is {today_str}.
When a user asks about trains between two stations:
1. Convert city/station names into their official Indian Railways station codes (e.g., New Delhi -> NDLS, Kanpur -> CNB, Ghaziabad -> GZB, Lucknow -> LKO, Mumbai Central -> MMCT, Howrah -> HWH) if the user didn't give codes.
2. Convert relative dates (like 'tomorrow' or 'this Friday') into YYYY-MM-DD format using today's date ({today_str}).
3. If the user forgot to mention source, destination, or travel date, politely ask for the missing detail before calling the tool.
4. Present the train options in a clean, easy-to-read Markdown table showing Train Number, Train Name, Departure, Arrival, and Duration.
"""

def create_chat(client, model_name: str, history=None):
    return client.chats.create(
        model=model_name,
        history=history,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[get_trains_between_stations],
            temperature=0.2,
        ),
    )

# 3. Initialize session state so chat memory persists across browser interactions
if "client" not in st.session_state:
    st.session_state.client = genai.Client()
    st.session_state.model_idx = 0
    st.session_state.chat = create_chat(st.session_state.client, MODELS[0])
    st.session_state.messages = []

# Optional sidebar with active model info & a Clear Chat button
with st.sidebar:
    st.subheader("Agent Status")
    st.info(f"**Active Model:** `{MODELS[st.session_state.model_idx]}`")
    if st.button("Clear Conversation"):
        st.session_state.model_idx = 0
        st.session_state.chat = create_chat(st.session_state.client, MODELS[0])
        st.session_state.messages = []
        st.rerun()

# 4. Render previous messages in the chat window
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Handle new user input from the chat box
if prompt := st.chat_input("Where would you like to travel?"):
    # Display user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate agent response with automatic 503/504 fallback
    with st.chat_message("assistant"):
        with st.spinner("Checking live IRCTC schedules..."):
            while True:
                try:
                    response = st.session_state.chat.send_message(prompt)
                    reply = response.text
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    break
                except errors.ServerError as e:
                    if e.code in (503, 504) and st.session_state.model_idx + 1 < len(MODELS):
                        old_history = st.session_state.chat.get_history()
                        st.session_state.model_idx += 1
                        fallback_model = MODELS[st.session_state.model_idx]
                        st.toast(f"Primary model busy ({e.code}). Switched to {fallback_model}.")
                        st.session_state.chat = create_chat(
                            st.session_state.client, fallback_model, history=old_history
                        )
                    else:
                        st.error(f"Server error ({e.code}): Please try again in a moment.")
                        break