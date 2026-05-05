import streamlit as st
from src.utils import Message

st.title(Message("home_title").text)

st.page_link("pages/1_hqm.py", label=Message("hqm_title").text, icon="📖")

st.divider()

st.subheader("About")
st.write("[![GitHub Release](https://img.shields.io/github/v/release/peunsu/mc-questing-mod-localizer?style=for-the-badge)](https://github.com/peunsu/mc-questing-mod-localizer/releases/latest)")
st.write(Message("home_about").text)

st.subheader(Message("home_title_1").text)
st.write(Message("home_desc_1").text)

st.subheader(Message("home_title_2").text)
st.write(Message("home_desc_2").text)

st.subheader(Message("home_contact_title").text)
st.write("* [GitHub](https://github.com/peunsu/mc-questing-mod-localizer)")
st.write("* [Email](mailto:peunsu55@gmail.com)")

st.subheader("License")
st.write("[MIT License](https://github.com/peunsu/mc-questing-mod-localizer/blob/main/LICENSE) ⓒ 2024-2025 [peunsu](https://github.com/peunsu)")
