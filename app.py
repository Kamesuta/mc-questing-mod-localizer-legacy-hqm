import asyncio
import logging

import streamlit as st

from src.utils import Message

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.getLogger("httpx").setLevel(logging.WARNING)  # Suppress httpx logs

hqm_page = st.Page("pages/1_hqm.py", title="HQM Localizer", icon="📖")
lexicon_wrap_page = st.Page("pages/2_lexicon_wrap.py", title="Lexicon Wrapper", icon="📚")

pg = st.navigation(
    {
        "Hardcore Questing Mode": [hqm_page],
        "Language Utilities": [lexicon_wrap_page],
    },
    position='top'
)

st.logo("static/logo.png", icon_image="static/icon.png")

st.set_page_config(
        page_title = "Minecraft Questing Mod Localizer",
        page_icon = "https://static.wikia.nocookie.net/minecraft_gamepedia/images/e/e9/Book_and_Quill_JE2_BE2.png",
        menu_items = {
            "Get help": "https://github.com/Kamesuta/mc-questing-mod-localizer-legacy-hqm",
            "Report a Bug": "https://github.com/Kamesuta/mc-questing-mod-localizer-legacy-hqm/issues",
            "About": '''
            ### HQM Localizer (Legacy)\n
            [![GitHub Release](https://img.shields.io/github/v/release/Kamesuta/mc-questing-mod-localizer-legacy-hqm?style=for-the-badge)](https://github.com/Kamesuta/mc-questing-mod-localizer-legacy-hqm/releases/latest)\n
            **[MIT License](https://github.com/Kamesuta/mc-questing-mod-localizer-legacy-hqm/blob/main/LICENSE) ⓒ 2024-2025 [peunsu](https://github.com/peunsu), [Kamesuta](https://github.com/Kamesuta)**\n
            ### Credits\n
            * **Hardcore Questing Mode**\n
            ### Dependencies\n
            * [streamlit](https://github.com/streamlit/streamlit): A tool to build and share the web application with Python.
            * [googletrans](https://github.com/ssut/py-googletrans): Google translate API for Python.
            * [deepl-python](https://github.com/DeepLcom/deepl-python): DeepL API client for Python.
            * [langchain](https://github.com/langchain-ai/langchain): A framework for developing applications powered by language models.
            '''
        }
    )

if st.context.locale in ("ko-KR", "ko"):
    st.session_state.language = "ko-KR"
else:
    st.session_state.language = "en-US"

with st.sidebar:
    language_selector = st.pills(
        "Site Language",
        options=["en-US", "ko-KR"],
        selection_mode="single",
        default=st.session_state.language,
        format_func=lambda x: {
            "en-US": "English",
            "ko-KR": "한국어",
        }[x]
    )
    st.session_state.language = language_selector
    
    st.text_input(
        label = Message("deepl_key_label").text,
        type = "password",
        key = "deepl_key",
        help = Message("deepl_key_help").text
    )
    st.text_input(
        label = Message("gemini_key_label").text,
        type = "password",
        key = "gemini_key",
        help = Message("gemini_key_help").text
    )
    st.text_input(
        label = Message("openai_key_label").text,
        type = "password",
        key = "openai_key",
        help = Message("openai_key_help").text
    )
    Message("api_key_caption").caption()

if "tasks" not in st.session_state:
    st.session_state.tasks = {}

try:
    st.session_state.loop = asyncio.get_running_loop()
except RuntimeError:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

pg.run()
