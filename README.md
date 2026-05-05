# HQM Localizer

HQM Localizer is a Streamlit web app for translating Hardcore Questing Mode 1.7.10 `quests.hqm` files.

This project is a fork of https://github.com/peunsu/mc-questing-mod-localizer, specialized for HQM’s legacy format.

It reads HQM's bit-packed binary quest format, extracts translatable text to JSON, translates it using a selected service, and writes the result back into a new `quests.hqm`.

## Supported Format

- Hardcore Questing Mode 1.7.10
- `quests.hqm`

## Installation

Python 3.10 is required.

```bash
git clone https://github.com/Kamesuta/mc-questing-mod-localizer-legacy-hqm
cd mc-questing-mod-localizer-legacy-hqm
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- Always keep a backup of the original `quests.hqm`.
- To prevent mojibake in Minecraft, add `-Dfile.encoding=UTF-8` to JVM arguments.
- HQM has strict byte limits; long translations may be truncated.
- This tool writes directly into `.hqm` and does not use external language files.
