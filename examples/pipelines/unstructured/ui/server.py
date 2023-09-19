import os

import requests
import streamlit as st
from dotenv import load_dotenv

with st.sidebar:
    st.markdown(
        "[View the source code on GitHub](https://github.com/pathwaycom/llm-app)"
    )

# Load environment variables
load_dotenv()
api_host = os.environ.get("PATHWAY_REST_CONNECTOR_HOST", "127.0.0.1")
api_port = int(os.environ.get("PATHWAY_REST_CONNECTOR_PORT", 8080))
data_path = "../../../../examples/data/finance/"

# Streamlit UI elements
st.title("LLM App")

uploaded_files = st.file_uploader("Upload a text file", accept_multiple_files=True)
if uploaded_files:
    for file in uploaded_files:
        print(file.name)
        with open(os.path.join(data_path, file.name), "wb") as f:
            f.write(file.read())

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# React to user input
if prompt := st.chat_input("How can I help you today?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    url = f"http://{api_host}:{api_port}/"
    data = {"query": prompt, "user": "user"}

    response = requests.post(url, json=data)

    if response.status_code == 200:
        response = response.json()
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.error(
            f"Failed to send data to Discounts API. Status code: {response.status_code}"
        )
