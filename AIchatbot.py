import streamlit as st
import pickle
import os
import datetime
import time
import uuid
import google.generativeai as genai

# --- Gemini Config ---
GEMINI_API_KEY = "AIzaSyCHBFK22JYLT5Mg6Xmf-QP1HS8tMYhBfn4"   # ضع المفتاح الحقيقي هنا
GEMINI_MODEL = "gemini-2.5-flash"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

# File to save all chats
chats_file = "all_chats.pkl"

# Load chats
if os.path.exists(chats_file):
    with open(chats_file, "rb") as f:
        all_chats = pickle.load(f)
else:
    all_chats = {}

# Session state
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

def save_all_chats():
    with open(chats_file, "wb") as f:
        pickle.dump(all_chats, f)

def get_ai_response(messages):
    """Send conversation history to Gemini"""
    # Gemini expects only the text context, so join messages
    history = ""
    for msg in messages:
        if msg["role"] == "user":
            history += f"User: {msg['content']}\n"
        elif msg["role"] == "assistant":
            history += f"Assistant: {msg['content']}\n"

    try:
        response = model.generate_content(history + "\nAssistant:")
        return response.text
    except Exception as e:
        return f"Unexpected error: {e}"

def get_chat_title(chat):
    """Return chat title based on first user message"""
    for msg in chat:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content", "")
            return content[:30] + ("..." if len(content) > 30 else "")
    return "New Chat"


# --- Streamlit UI ---
st.set_page_config(page_title="Gemini Chatbot", page_icon="💬", layout="wide")
st.title("Your helpful Chatbot")

# Sidebar
st.sidebar.header("Chats")

# New chat button
if st.sidebar.button("➕ New Chat"):
    new_id = str(uuid.uuid4())
    all_chats[new_id] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    st.session_state.chat_id = new_id
    save_all_chats()
    st.rerun()

# List existing chats with delete option
for chat_id, chat in list(all_chats.items()):
    title = get_chat_title(chat)
    col1, col2 = st.sidebar.columns([4, 2])
    with col1:
        # Click title to open chat
        if st.button(title, key=f"open_{chat_id}"):
            st.session_state.chat_id = chat_id
            st.rerun()
    with col2:
        if st.button("Delete", key=f"delete_{chat_id}"):
            del all_chats[chat_id]
            if st.session_state.chat_id == chat_id:
                st.session_state.chat_id = None
            save_all_chats()
            st.rerun()

# If no chat selected, pick the first available
if st.session_state.chat_id is None and all_chats:
    st.session_state.chat_id = list(all_chats.keys())[0]

# Current chat
if st.session_state.chat_id is None:
    st.info("Start a new chat from the sidebar.")
    st.stop()
else:
    messages = all_chats[st.session_state.chat_id]
    if isinstance(messages, dict) and "messages" in messages:
        messages = messages["messages"]
        all_chats[st.session_state.chat_id] = messages

# Display chat history
for msg in messages:
    if not isinstance(msg, dict):  # skip corrupted
        continue
    if msg.get("role") == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg.get("content", ""))

# Chat input
if user_input := st.chat_input("Type your message..."):
    # Add user input
    messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Handle quick answers
    if "time" in user_input.lower():
        ai_reply = f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}"
    elif "date" in user_input.lower():
        ai_reply = f"Today's date is {datetime.date.today().strftime('%B %d, %Y')}"
    else:
        # Gemini response
        ai_reply = get_ai_response(messages)

    # Display AI reply
    messages.append({"role": "assistant", "content": ai_reply})
    with st.chat_message("assistant"):
        st.markdown(ai_reply)

    # Save
    all_chats[st.session_state.chat_id] = messages
    save_all_chats()
