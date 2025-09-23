import streamlit as st
import pickle
import os
import datetime
import time
import uuid
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ServiceResponseError

# Azure config
endpoint = "https://models.github.ai/inference"
token = "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"
client = ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(token))

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
    retries = 3
    for attempt in range(retries):
        try:
            response = client.complete(
                model="gpt-4o-mini",
                messages=messages
            )
            return response.choices[0].message.content
        except ServiceResponseError:
            time.sleep(2)
        except Exception as e:
            return f"Unexpected error: {e}"
    return "Failed to connect after several retries."

def get_chat_title(chat):
    """Return chat title based on first user message"""
    for msg in chat:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content", "")
            return content[:30] + ("..." if len(content) > 30 else "")
    return "New Chat"


# --- Streamlit UI ---
st.set_page_config(page_title="Azure Chatbot", page_icon="💬", layout="wide")
st.title("💬 Azure Chatbot with Multiple Chats")

# Sidebar
st.sidebar.header("📂 Chats")

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
    col1, col2 = st.sidebar.columns([4, 1])
    with col1:
        # Click title to open chat
        if st.button(title, key=f"open_{chat_id}"):
            st.session_state.chat_id = chat_id
            st.rerun()
    with col2:
        if st.button("🗑️", key=f"delete_{chat_id}"):
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
    # 🔹 Fix: if stored as dict, extract the list
    if isinstance(messages, dict) and "messages" in messages:
        messages = messages["messages"]
        all_chats[st.session_state.chat_id] = messages


# Display chat history
# Display chat history
for msg in messages:
    if not isinstance(msg, dict):  # skip corrupted/invalid messages
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
        # AI response
        ai_reply = get_ai_response(messages)

    # Display AI reply
    messages.append({"role": "assistant", "content": ai_reply})
    with st.chat_message("assistant"):
        st.markdown(ai_reply)

    # Save
    all_chats[st.session_state.chat_id] = messages
    save_all_chats()

##############################################################################################################################
# import streamlit as st
# import pickle
# import os
# import datetime
# import time
# import uuid

# # GitHub Models API config
# client = OpenAI(
#     base_url="https://models.github.ai/inference",
#     api_key="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"  # replace with your GitHub token
# )

# # File to save all chats
# chats_file = "all_chats.pkl"

# # Load chats
# if os.path.exists(chats_file):
#     with open(chats_file, "rb") as f:
#         all_chats = pickle.load(f)
# else:
#     all_chats = {}

# # Session state
# if "chat_id" not in st.session_state:
#     st.session_state.chat_id = None

# def save_all_chats():
#     with open(chats_file, "wb") as f:
#         pickle.dump(all_chats, f)

# def get_ai_response(messages):
#     """Send chat to GitHub Models"""
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=messages
#         )
#         return response.choices[0].message.content
#     except Exception as e:
#         return f"Unexpected error: {e}"

# def default_chat_title(messages):
#     """Generate a title from the first user message if no title is set"""
#     for msg in messages:
#         if msg["role"] == "user":
#             return msg["content"][:30] + ("..." if len(msg["content"]) > 30 else "")
#     return "New Chat"

# # --- Streamlit UI ---
# st.set_page_config(page_title="Chatbot", page_icon="💬", layout="wide")
# st.title("💬 Chatbot with Multiple Chats")

# # Sidebar
# st.sidebar.header("📂 Chats")

# # New chat button
# if st.sidebar.button("➕ New Chat"):
#     new_id = str(uuid.uuid4())
#     all_chats[new_id] = {
#         "title": "New Chat",
#         "messages": [{"role": "system", "content": "You are a helpful assistant."}]
#     }
#     st.session_state.chat_id = new_id
#     save_all_chats()
#     st.rerun()

# # List existing chats with rename + delete
# for chat_id, chat_data in list(all_chats.items()):
#     # Handle both dict (new format) and list (old format)
#     if isinstance(chat_data, dict):
#         title = chat_data.get("title") or default_chat_title(chat_data["messages"])
#     else:
#         # old format: list of messages
#         title = default_chat_title(chat_data)
#         all_chats[chat_id] = {"title": title, "messages": chat_data}
#         chat_data = all_chats[chat_id]
#         save_all_chats()

#     col1, col2 = st.sidebar.columns([4, 2])
#     with col1:
#         if st.button(title, key=f"open_{chat_id}"):  # title itself is clickable
#             st.session_state.chat_id = chat_id
#             st.rerun()

#     with col2:
#         if st.button("Delete", key=f"delete_{chat_id}"):
#             del all_chats[chat_id]
#             if st.session_state.chat_id == chat_id:
#                 st.session_state.chat_id = None
#             save_all_chats()
#             st.rerun()

# # If no chat selected, pick the first available
# if st.session_state.chat_id is None and all_chats:
#     st.session_state.chat_id = list(all_chats.keys())[0]

# # Current chat
# if st.session_state.chat_id is None:
#     st.info("Start a new chat from the sidebar.")
#     st.stop()
# else:
#     chat_data = all_chats[st.session_state.chat_id]
#     messages = chat_data["messages"]

# # Display chat history
# for msg in messages:
#     if msg["role"] == "system":
#         continue
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # Chat input
# if user_input := st.chat_input("Type your message..."):
#     # Add user input
#     messages.append({"role": "user", "content": user_input})
#     with st.chat_message("user"):
#         st.markdown(user_input)

#     # Handle quick answers
#     if "time" in user_input.lower():
#         ai_reply = f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}"
#     elif "date" in user_input.lower():
#         ai_reply = f"Today's date is {datetime.date.today().strftime('%B %d, %Y')}"
#     else:
#         # AI response
#         ai_reply = get_ai_response(messages)

#     # Display AI reply
#     messages.append({"role": "assistant", "content": ai_reply})
#     with st.chat_message("assistant"):
#         st.markdown(ai_reply)

#     # Save
#     all_chats[st.session_state.chat_id]["messages"] = messages
#     save_all_chats()
