import streamlit as st

from src.utils import Message, read_file, write_file
from tools.format_aura_pages import format_lang_text


# 説明書本文の接頭辞をプリセットとしてまとめる。
PREFIX_PRESETS = {
    "aura.page.": "Aura-Cascade (`aura.page.*`)",
    "botania.page.": "Botania (`botania.page.*`)",
}


Message("lexicon_wrap_title").title()

st.divider()
Message("lexicon_wrap_readme").info()

with st.container(border=True):
    Message("upload_lang_header").subheader()
    lang_file = st.file_uploader(
        label=Message("lexicon_wrap_upload_label").text,
        type=["lang"],
        accept_multiple_files=False,
    )

if not lang_file:
    st.stop()

with st.container(border=True):
    Message("settings_header").subheader()

    preset_options = ["Aura-Cascade", "Botania", "Aura-Cascade + Botania", "Custom"]
    preset = st.selectbox(
        label=Message("lexicon_wrap_preset_label").text,
        options=preset_options,
        index=2,
    )

    # よく使うパターンを先頭に置き、必要なら手動接頭辞も許可する。
    if preset == "Aura-Cascade":
        prefixes = ["aura.page."]
    elif preset == "Botania":
        prefixes = ["botania.page."]
    elif preset == "Aura-Cascade + Botania":
        prefixes = ["aura.page.", "botania.page."]
    else:
        custom_prefixes = st.text_input(
            label=Message("lexicon_wrap_custom_prefix_label").text,
            value="aura.page.,botania.page.",
        )
        prefixes = [prefix.strip() for prefix in custom_prefixes.split(",") if prefix.strip()]

    separator_mode = st.radio(
        label=Message("lexicon_wrap_separator_label").text,
        options=["space", "br"],
        horizontal=True,
        index=0,
        format_func=lambda value: {
            "space": Message("lexicon_wrap_separator_space").text,
            "br": Message("lexicon_wrap_separator_br").text,
        }[value],
    )

    # 日本語本文前提の既定値。必要なら手動調整できるようにする。
    width = st.number_input(
        label=Message("lexicon_wrap_width_label").text,
        min_value=1,
        max_value=80,
        value=13,
        step=1,
    )
    ascii_width = st.number_input(
        label=Message("lexicon_wrap_ascii_width_label").text,
        min_value=0.1,
        max_value=2.0,
        value=0.6,
        step=0.1,
    )
    normalize_existing_breaks = st.checkbox(
        label=Message("lexicon_wrap_normalize_label").text,
        value=True,
    )

separator = " " if separator_mode == "space" else "<br>"

button = st.button(
    label=Message("start_button_label").text,
    type="primary",
    use_container_width=True,
)

if not button:
    st.stop()

source_text = read_file(lang_file)
result_text = source_text

for prefix in prefixes:
    # プリセットごとに順番に整形する。
    result_text = format_lang_text(
        result_text,
        prefix=prefix,
        width=width,
        ascii_width=ascii_width,
        normalize_existing_breaks=normalize_existing_breaks,
        separator=separator,
    )

with st.container(border=True):
    Message("downloads_header").subheader()

    download_name = lang_file.name
    if download_name.lower().endswith(".lang"):
        download_name = download_name[:-5] + ".wrapped.lang"
    else:
        download_name = download_name + ".wrapped.lang"

    st.download_button(
        label=download_name,
        data=write_file(result_text),
        file_name=download_name,
        on_click="ignore",
        mime="text/plain",
    )

with st.container(border=True):
    Message("lexicon_wrap_preview_header").subheader()
    st.text_area(
        label=Message("lexicon_wrap_preview_label").text,
        value=result_text,
        height=320,
    )
