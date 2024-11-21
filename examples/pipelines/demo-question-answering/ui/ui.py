# Copyright © 2024 Pathway

import logging
import os

import requests
import streamlit as st
from dotenv import load_dotenv
from pathway.xpacks.llm.question_answering import RAGClient

load_dotenv()

PATHWAY_HOST = os.environ.get("PATHWAY_HOST", "app")
PATHWAY_PORT = os.environ.get("PATHWAY_PORT", 8000)

st.set_page_config(page_title="Pathway RAG App", page_icon="favicon.ico")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)

logger = logging.getLogger("streamlit")
logger.setLevel(logging.INFO)

conn = RAGClient(url=f"http://{PATHWAY_HOST}:{PATHWAY_PORT}")

note = """
<H4><b>Ask a question"""
st.markdown(note, unsafe_allow_html=True)

st.markdown(
    """
<style>
div[data-baseweb="base-input"]{
}
input[class]{
font-size:150%;
color: black;}
button[data-testid="baseButton-primary"], button[data-testid="baseButton-secondary"]{
    border: none;
    display: flex;
    background-color: #E7E7E7;
    color: #454545;
    transition: color 0.3s;
}
button[data-testid="baseButton-primary"]:hover{
    color: #1C1CF0;
    background-color: rgba(28,28,240,0.3);
}
button[data-testid="baseButton-secondary"]:hover{
    color: #DC280B;
    background-color: rgba(220,40,11,0.3);
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="baseButton-primary"]){
    display: flex;
    flex-direction: column;
    z-index: 0;
    width: 3rem;

    transform: translateY(-500px) translateX(672px);
}
</style>
""",
    unsafe_allow_html=True,
)


question = st.text_input(label="", placeholder="Ask your question?")


def get_options_list(metadata_list: list[dict], opt_key: str) -> list:
    """Get all available options in a specific metadata key."""
    options = set(map(lambda x: x[opt_key], metadata_list))
    return list(options)


logger.info("Requesting pw_list_documents...")
document_meta_list = conn.pw_list_documents(keys=[])
logger.info("Received response pw_list_documents")

st.session_state["document_meta_list"] = document_meta_list

available_files = get_options_list(st.session_state["document_meta_list"], "path")


with st.sidebar:
    st.info(
        body="See the source code [here](https://github.com/pathwaycom/llm-app/tree/main/examples/pipelines/demo-question-answering).",  # noqa: E501
        icon=":material/code:",
    )

    file_names = [i.split("/")[-1] for i in available_files]

    markdown_table = "| Indexed files |\n| --- |\n"
    for file_name in file_names:
        markdown_table += f"| {file_name} |\n"
    st.markdown(markdown_table, unsafe_allow_html=True)

    st.button("⟳ Refresh", use_container_width=True)

css = """
<style>
.slider-container {
    margin-top: 20px; /* Add some space between the main image and the slider */
}

.slider-item {
    float: left;
    margin: 10px;
    width: 120px; /* Adjust the width to your liking */
    // height: 50px; /* Adjust the height to your liking */
    border: 1px solid #ccc;
    border-radius: 5px;
    cursor: pointer;
}

.slider-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 5px;
}

.slider-wrapper {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
}

.slider-item {
    margin: 10px;
}

</style>"""


st.markdown(css, unsafe_allow_html=True)


def send_post_request(
    url: str, data: dict, headers: dict = {}, timeout: int | None = None
):
    response = requests.post(url, json=data, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


if question:
    logger.info(
        {
            "_type": "search_request_event",
            "query": question,
        }
    )

    api_url = f"http://{PATHWAY_HOST}:{PATHWAY_PORT}/v1/pw_ai_answer"
    payload = {
        "prompt": question,
        "response_type": "long",
    }
    with st.spinner("Retrieving response..."):
        response = send_post_request(api_url, payload)

    # response = conn.pw_ai_answer(question)

    logger.info(
        {
            "_type": "search_response_event",
            "query": question,
            "response": type(response),
        }
    )

    logger.info(type(response))

    st.markdown(f"**Answering question:** {question}")
    st.markdown(f"""{response}""")
