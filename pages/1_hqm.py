import copy
import json
import time

import streamlit as st

from src.constants import MINECRAFT_LANGUAGES
from src.hqm_binary import HQMQuestConverter
from src.translator import TranslationManager, get_translator_cls
from src.utils import *


Message("hqm_title").title()

st.divider()
Message("hqm_readme").info()

with st.form("hqm_task_form"):
    Message("modpack_name_header").subheader()
    modpack_name = st.text_input(
        label=Message("modpack_name_label").text,
        max_chars=32,
        placeholder="simply_magic",
    )

    Message("select_task_header").subheader()
    task = st.radio(
        label=Message("select_task_label").text,
        options=[0, 1, 2],
        format_func=lambda x: {
            0: Message("hqm_task_convert_translate").text,
            1: Message("hqm_task_extract_only").text,
            2: Message("hqm_task_apply_translation").text,
        }[x],
        key="hqm_task",
    )

    task_submit = st.form_submit_button()
    if not task_submit and not st.session_state.get("hqm_task_submit"):
        st.stop()
    st.session_state.hqm_task_submit = True

with st.container(border=True):
    Message("upload_quest_header").subheader()
    quest_file = st.file_uploader(
        label=Message("upload_quest_label_hqm").text,
        type=["hqm"],
        accept_multiple_files=False,
    )

    translation_file = None
    if task == 2:
        Message("upload_lang_header").subheader()
        translation_file = st.file_uploader(
            label=Message("upload_lang_label_hqm").text,
            type=["json"],
            accept_multiple_files=False,
        )

if not quest_file:
    st.stop()
if task == 2 and not translation_file:
    st.stop()

with st.container(border=True):
    Message("settings_header").subheader()

    if task == 0:
        translator_service = st.pills(
            label=Message("select_translator_label").text,
            options=["Google", "DeepL", "Gemini", "OpenAI"],
            default="Google",
            key="translator_service",
        )
        translator_cls, auth_key = get_translator_cls(translator_service)
        check_auth_key(translator_cls, auth_key)
        translator = translator_cls(auth_key)
        lang_list = translator.lang_list
    else:
        lang_list = list(MINECRAFT_LANGUAGES)

    source_lang = st.selectbox(
        label=Message("select_source_lang_label").text,
        options=lang_list,
        index=lang_list.index("en_us"),
        format_func=lambda x: f"{x} ({MINECRAFT_LANGUAGES[x]})",
    )

    if task == 0:
        target_lang = st.selectbox(
            label=Message("select_target_lang_label").text,
            options=lang_list,
            index=lang_list.index("ja_jp") if "ja_jp" in lang_list else lang_list.index("en_us"),
            format_func=lambda x: f"{x} ({MINECRAFT_LANGUAGES[x]})",
        )
        if source_lang == target_lang:
            Message("select_same_lang", stop=True).warning()

button = st.button(
    label=Message("start_button_label").text,
    type="primary",
    use_container_width=True,
    key="running",
    disabled=st.session_state.get("running", False),
)

if button:
    status = st.status(label=Message("status_in_progress").text, expanded=True)
    converter = HQMQuestConverter()
    translated_hqm = None
    source_lang_dict = {}
    target_lang_dict = {}
    warnings = []
    task_key = None

    try:
        Message("status_step_1", st_container=status).send()
        hqm_file, source_lang_dict = converter.extract(modpack_name, quest_file)
        status.write(Message("hqm_status_extracted", count=len(source_lang_dict)).text)

        if task == 0:
            Message("status_step_2", st_container=status).send()
            translation_manager = TranslationManager(translator)
            target_lang_dict = copy.deepcopy(source_lang_dict)
            if source_lang_dict:
                task_key = f"task-{generate_task_key(time.time())}"
                schedule_task(
                    task_key,
                    translation_manager(source_lang_dict, target_lang_dict, target_lang, status),
                )
                process_tasks()
            warnings = hqm_file.apply_lang_dict(modpack_name, target_lang_dict)
            translated_hqm = hqm_file.to_bytes()
        elif task == 2:
            target_lang_dict = json.loads(read_file(translation_file))
            warnings = hqm_file.apply_lang_dict(modpack_name, target_lang_dict)
            translated_hqm = hqm_file.to_bytes()

        if warnings:
            status.warning(Message("hqm_truncation_warning", count=len(warnings)).text)
            status.code("\n".join(warnings[:200]), language=None, line_numbers=True, height=240)
    except Exception as e:
        status.update(label=Message("status_error").text, state="error")
        status.error(f"An error occurred while localizing: {e}")
        st.stop()
    finally:
        if task_key and task_key in st.session_state.tasks:
            del st.session_state.tasks[task_key]

    status.update(label=Message("status_done").text, state="complete")

    with st.container(border=True):
        Message("downloads_header").subheader()

        source_lang_filename = f"{source_lang}.json"
        st.download_button(
            label=source_lang_filename,
            data=json.dumps(source_lang_dict, indent=4, ensure_ascii=False),
            file_name=source_lang_filename,
            on_click="ignore",
            mime="application/json",
        )

        if task == 0:
            target_lang_filename = f"{target_lang}.json"
            st.download_button(
                label=target_lang_filename,
                data=json.dumps(target_lang_dict, indent=4, ensure_ascii=False),
                file_name=target_lang_filename,
                on_click="ignore",
                mime="application/json",
            )

        if translated_hqm is not None:
            st.download_button(
                label="quests.hqm",
                data=translated_hqm,
                file_name="quests.hqm",
                on_click="ignore",
                mime="application/octet-stream",
            )

    with st.container(border=True):
        Message("user_guide_header").subheader()
        if task == 1:
            Message("hqm_user_guide_extract").send()
        else:
            Message("hqm_user_guide_apply").send()
