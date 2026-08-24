import streamlit as st
from bedrock_chat import create_retrieval_qa, get_answer  # Replace with your logic

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "qa" not in st.session_state or "memory" not in st.session_state:
    qa, memory = create_retrieval_qa()
    st.session_state.qa = qa
    st.session_state.memory = memory

st.markdown(
    """
    <style>
    body {
        background-color: #121212;
        color: #ffffff;
    }
    .main {
        background-color: #121212;
    }
    .chat-bubble {
        padding: 10px;
        margin: 10px 0;
        border-radius: 10px;
        max-width: 75%;
    }
    .user-bubble {
        background-color: #1E88E5;
        color: #ffffff;
        margin-left: auto;
    }
    .bot-bubble {
        background-color: #424242;
        color: #ffffff;
        margin-right: auto;
    }
    .stTextInput > div > div {
        background-color: #ffffff; /* White background */
        border: 1px solid #444;
        color: #000000; 
    }
    input {
        color: #000000 !important; 
    }
    .stButton > button {
        background-color: #1E88E5;
        color: #ffffff;
        border: none;
        border-radius: 5px;
    }
    .stButton > button:hover {
        background-color: #1565C0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("SageMaker vs. Bedrock")

# Display chat history
for message in st.session_state.chat_history:
    if message["sender"] == "User":
        st.markdown(
            f'<div class="chat-bubble user-bubble">{message["content"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="chat-bubble bot-bubble">{message["content"]}</div>',
            unsafe_allow_html=True,
        )
st.markdown("</div>", unsafe_allow_html=True)

# Input field for user query
with st.form("chat_form", clear_on_submit=True):
    query = st.text_input("Type your message:", key="user_query")
    submit_button = st.form_submit_button("Send")

    if submit_button and query:
        # Append user query to chat history
        st.session_state.chat_history.append({"sender": "User", "content": query})
        st.markdown(
            f'<div class="chat-bubble user-bubble">{query}</div>',
            unsafe_allow_html=True,
        )
        
        # Get the bot's response
        answer = get_answer(query, st.session_state.qa, st.session_state.memory)
        
        # Append bot response to chat history
        st.session_state.chat_history.append({"sender": "Bot", "content": answer})

        st.rerun()