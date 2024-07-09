# flake8 ignore:E501
import logging
import os
import urllib.parse
from itertools import cycle

import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pathway.xpacks.llm.question_answering import RAGClient

load_dotenv()

PATHWAY_HOST = os.environ.get(
    "PATHWAY_NW_HOST", "pathway_app"
)  # set in the network settings of docker-compose
PATHWAY_PORT = os.environ.get("PATHWAY_PORT", 8000)

FILE_SERVER_BASE_URL = os.environ.get("FILE_SERVER_URL", "http://file_server:8080/")
DOCKER_FILE_SV_BASE_URL = "http://file_server:8080/documents"  # for internal requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)

st.set_page_config(page_title="Find the right slide")  # ,page_icon="favicon.ico"


logger = logging.getLogger("streamlit")
logger.setLevel(logging.INFO)

conn = RAGClient(url=f"http://{PATHWAY_HOST}:{PATHWAY_PORT}")


file_server_image_base_url = f"{FILE_SERVER_BASE_URL}images"

file_server_pdf_base_url = f"{FILE_SERVER_BASE_URL}documents"


note = """
<H4><b>Search your slide decks"""
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

question = st.text_input(label="", placeholder="Why buy")


def get_options_list(metadata_list: list[dict], opt_key: str) -> list:
    """Get all available options in a specific metadata key."""
    options = set(map(lambda x: x[opt_key], metadata_list))
    return list(options)


def get_image_serve_url(metadata: dict) -> str:
    slide_name_enc, page, tot_pages = (
        metadata["slide_id"].replace(".png", "").split("_")
    )

    page, tot_pages = int(page), int(tot_pages)
    name = f"{slide_name_enc}_{page}_{tot_pages}.png"
    base_url: str = file_server_image_base_url
    return f"{base_url}/{name}"


def get_adjacent_image_urls(metadata: dict) -> list[str]:
    logger.info(
        {"_type": "create_adjacent_image_urls", "slide_id": metadata["slide_id"]}
    )
    slide_name_enc, page, tot_pages = (
        metadata["slide_id"].replace(".png", "").split("_")
    )
    base_url: str = file_server_image_base_url

    page, tot_pages = int(page), int(tot_pages)

    ret_images = []

    if page > 1:
        prev_img_name = f"{base_url}/{slide_name_enc}_{page - 2}_{tot_pages}.png"
        ret_images.append(prev_img_name)

    if page > 0:
        prev_img_name = f"{base_url}/{slide_name_enc}_{page - 1}_{tot_pages}.png"
        ret_images.append(prev_img_name)

    cur_img_name = f"{base_url}/{slide_name_enc}_{page}_{tot_pages}.png"
    ret_images.append(cur_img_name)

    if page + 1 < tot_pages:
        next_img_name = f"{base_url}/{slide_name_enc}_{page + 1}_{tot_pages}.png"
        ret_images.append(next_img_name)

    if page + 2 < tot_pages:
        next_img_name = f"{base_url}/{slide_name_enc}_{page + 2}_{tot_pages}.png"
        ret_images.append(next_img_name)

    return ret_images


st.session_state["available_categories"] = None
st.session_state["available_languages"] = None

logger.info("Requesting pw_list_documents...")
document_meta_list = conn.pw_list_documents(keys=None)
logger.info("Received response pw_list_documents")

st.session_state["document_meta_list"] = document_meta_list


available_categories = get_options_list(document_meta_list, "category")
st.session_state["available_categories"] = available_categories

available_languages = get_options_list(document_meta_list, "language")
st.session_state["available_languages"] = available_languages


available_files = get_options_list(st.session_state["document_meta_list"], "path")


def get_slide_link(file_name, page_num=None) -> str:
    filename_encoded = urllib.parse.quote(file_name)
    image_url = f"{file_server_pdf_base_url}/{filename_encoded}"
    if page_num is not None:
        image_url += f"#page={page_num}"
    return image_url


def get_all_drive_files() -> list[str]:
    logger.info("request get_all_drive_files")
    response = requests.get(DOCKER_FILE_SV_BASE_URL)
    logger.info("response get_all_drive_files")

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        file_links = [a["href"] for a in soup.find_all("a", href=True)]

        file_links = [link for link in file_links if not link.endswith("/")]
    else:
        file_links = []
    return file_links


# DRIVE_ID = os.environ.get("DRIVE_ID", "foo")
# DRIVE_URL = f"https://drive.google.com/drive/folders/{DRIVE_ID}"
# drive_htm = f"""
# <div style="display: flex; align-items: center; vertical-align: middle">
#     <a href="{DRIVE_URL}" style="text-decoration:none;">
#       <figure style="display: flex; vertical-align: middle; margin-right: 20px; align-items: center;">
#         <img src="./app/static/Google_Drive_logo.png" width="30" alt="Google Drive Logo">
#         <figcaption style="font-size: 18px; font-weight: bold; margin-left: 10px;">Connected Folder ⚡</figcaption>
#       </figure>
#     </a>
# </div>
# """

with st.sidebar:
    st.info(
        """This demo app only allows `PDF` and `PPTX` documents.
        For other file types, convert to `PDF` or contact **Pathway**."""
    )
    # st.markdown(drive_htm, unsafe_allow_html=True)
    file_names = [i.split("/")[-1] for i in available_files]
    links = [get_slide_link(i) for i in file_names]

    markdown_table = "| Slides Ready for Search |\n| --- |\n"
    for file_name, link in zip(file_names, links):
        markdown_table += f"| [{file_name}]({link}) |\n"
    st.markdown(markdown_table, unsafe_allow_html=True)

    all_drive_files = get_all_drive_files()
    all_drive_files = [urllib.parse.unquote(i) for i in all_drive_files]
    all_drive_files = [i for i in all_drive_files if i.endswith(".pdf")]
    logger.info(f"All drive files: {all_drive_files}\nIndexed files: {file_names}")
    currently_processing_files = set(all_drive_files) - set(file_names)

    st.markdown("\n\n", unsafe_allow_html=True)

    if currently_processing_files:
        markdown_table = "| Indexing in Progress |\n| --- |\n"

        links = [get_slide_link(i) for i in currently_processing_files]
        for file_name, link in zip(currently_processing_files, links):
            markdown_table += f"| [{file_name}]({link}) |\n"
        st.markdown(markdown_table, unsafe_allow_html=True)
    else:
        st.markdown("## No new files detected.")


category_options = st.session_state["available_categories"]

lang_options = st.session_state["available_languages"]

cols = cycle(st.columns(2))

with next(cols):
    cat_options = st.multiselect(
        "Filtered Categories",
        category_options or [],
        [],
        key="cat_selection",
        label_visibility="hidden",
        placeholder="Filtered Categories",
    )

with next(cols):
    language_options = st.multiselect(
        "Languages",
        lang_options or [],
        [],
        key="lang_selection",
        label_visibility="hidden",
        placeholder="Filtered Languages",
    )

with st.sidebar:
    cat_prefix = "cat_"

    logger.info("All category options: %s", category_options)

    selected_categories = category_options if len(cat_options) == 0 else cat_options

    logger.info("Selected categories: %s", selected_categories)

    lang_prefix = "lang_"

    selected_languages = (
        lang_options if len(language_options) == 0 else language_options
    )

    st.session_state.category_filter = selected_categories
    st.session_state.language_filter = selected_languages


def get_category_filter(category: str) -> str:
    return f"contains({str(category)}, category)"


# TODO: merge these
def get_language_filter(lang: str) -> str:
    return f"contains({str(lang)}, language)"


def combine_filters(*args: str | None) -> str:
    """Construct single jmespath filter with `&&` from number of filters."""
    return " && ".join([arg for arg in args if arg is not None])


icon_thumbs_up = '<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24"><path fill="currentColor" d="M7.493 18.5c-.425 0-.82-.236-.975-.632A7.5 7.5 0 0 1 6 15.125a7.47 7.47 0 0 1 1.602-4.634c.151-.192.373-.309.6-.397c.473-.183.89-.514 1.212-.924a9 9 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.5 4.5 0 0 0 .322-1.672V2.75A.75.75 0 0 1 15 2a2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218c-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715q.068.633.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H14.23a4.5 4.5 0 0 1-1.423-.23l-3.114-1.04a4.5 4.5 0 0 0-1.423-.23zm-5.162-7.773a12 12 0 0 0-.831 4.398a12 12 0 0 0 .52 3.507C2.28 19.482 3.105 20 3.994 20H4.9c.445 0 .72-.498.523-.898a9 9 0 0 1-.924-3.977c0-1.708.476-3.305 1.302-4.666c.245-.403-.028-.959-.5-.959H4.25c-.832 0-1.612.453-1.918 1.227"/></svg>'  # noqa: E501

icon_thumbs_down = '<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24"><path fill="currentColor" d="M15.73 5.5h1.035A7.47 7.47 0 0 1 18 9.625a7.47 7.47 0 0 1-1.235 4.125h-.148c-.806 0-1.533.446-2.031 1.08a9 9 0 0 1-2.861 2.4c-.723.384-1.35.956-1.653 1.715a4.5 4.5 0 0 0-.322 1.672v.633A.75.75 0 0 1 9 22a2.25 2.25 0 0 1-2.25-2.25c0-1.152.26-2.243.723-3.218c.266-.558-.107-1.282-.725-1.282H3.622c-1.026 0-1.945-.694-2.054-1.715A12 12 0 0 1 1.5 12.25c0-2.848.992-5.464 2.649-7.521C4.537 4.247 5.136 4 5.754 4H9.77a4.5 4.5 0 0 1 1.423.23l3.114 1.04a4.5 4.5 0 0 0 1.423.23m5.939 8.523c.536-1.362.831-2.845.831-4.398c0-1.22-.182-2.398-.52-3.507c-.26-.85-1.084-1.368-1.973-1.368H19.1c-.445 0-.72.498-.523.898c.591 1.2.924 2.55.924 3.977a8.96 8.96 0 0 1-1.302 4.666c-.245.403.028.959.5.959h1.053c.832 0 1.612-.453 1.918-1.227"/></svg>'  # noqa: E501


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


def get_ext_img_with_href(url, target_url, *args) -> str:
    width: int = 600
    margin = 20

    def get_img_html(dc):
        return f"""
        <div class="slider-item">
                    <img src="{dc['url']}" width="90" />
                </div>"""  # TODO: add href

    slider_images = "\n".join([get_img_html(dc) for dc in args])

    html_code = f"""
        <a href="{target_url}">
        <img style="display: block; margin: {margin}px auto {margin}px auto" loading="lazy" src="{url}" width="{width}" />
        </a>

        <div class="slider-container">
            <!-- Slider wrapper -->
            <div class="slider-wrapper">
                <!-- Slider items -->
                    {slider_images}
                <!-- Add more slider items here -->
            </div>
        </div>
        """  # noqa: E501
    return html_code


st.markdown(css, unsafe_allow_html=True)


def log_rate_answer(event, idx, kwargs):
    logger.info({"_type": "rate_event", "rating": event, "rank": idx, **kwargs})


if question:
    select_cat = st.session_state.category_filter
    select_lang = st.session_state.language_filter

    filter_ls = [get_category_filter(select_cat), get_language_filter(select_lang)]

    combined_query_filter = combine_filters(*filter_ls)

    logger.info(
        {
            "_type": "search_request_event",
            "filter": combined_query_filter,
            "query": question,
        }
    )

    response = conn.pw_ai_answer(question, filters=combined_query_filter)

    logger.info(
        {
            "_type": "search_response_event",
            "filter": combined_query_filter,
            "query": question,
            "response": type(response),
        }
    )

    if response:
        logger.info(type(response[0]))

        text_responses = [r["text"] for r in response]

        image_metadatas = [r["metadata"] for r in response]

        for m in image_metadatas:
            logger.info("Retrieved metadatas: %s || %s", m["language"], m["category"])

        st.markdown(f"**Searched for:** {question}")

        for idx, cur_metadata in enumerate(image_metadatas):
            file_name = cur_metadata["path"].split("/")[-1]

            select_page = cur_metadata["image_page"] + 1

            adjacent_urls = get_adjacent_image_urls(cur_metadata)

            args = [{"url": i} for i in adjacent_urls]

            image_html = get_ext_img_with_href(
                get_image_serve_url(cur_metadata),
                get_slide_link(file_name, select_page),
                *args,
            )

            image_url = get_slide_link(file_name, select_page)

            slide_id = cur_metadata["slide_id"]

            st.markdown(f"Page `{select_page}` of [`{file_name}`]({image_url})")

            st.markdown(image_html, unsafe_allow_html=True)

            log_args = (
                idx,
                {
                    "slide_id": slide_id,
                    "filter": combined_query_filter,
                    "query": question,
                    "file_name": file_name,
                    "selected_cat": select_cat,
                    "selected_lang": select_lang,
                },
            )
            col1, col2, col3 = st.columns([12, 1, 1])
            with col2:
                st.button(
                    "👍",
                    on_click=log_rate_answer,
                    type="primary",
                    key=slide_id + "_up",
                    args=("like", *log_args),
                )
            with col3:
                st.button(
                    "👎",
                    on_click=log_rate_answer,
                    type="secondary",
                    key=slide_id + "_down",
                    args=("dislike", *log_args),
                )

    else:
        st.markdown(
            f"""No results were found for search query: `{question}`
            and filter criteria: `{combined_query_filter}`"""
        )
