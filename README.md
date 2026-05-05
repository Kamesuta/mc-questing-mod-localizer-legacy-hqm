# HQM Localizer

HQM Localizer is a Streamlit web app for translating Hardcore Questing Mode 1.7.10 `quests.hqm` files.

It reads HQM's bit-packed binary quest format, extracts translatable text to JSON, translates it with a selected translation service, and writes the translated text back into a new `quests.hqm`.

## Supported Format

- Hardcore Questing Mode 1.7.10
- `quests.hqm`
- Tested with a `CUSTOM_PRECISION_TYPES` file version sample

## Installation

Python 3.10 is required.

```bash
git clone https://github.com/peunsu/mc-questing-mod-localizer
cd mc-questing-mod-localizer
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- Keep a backup of the original `quests.hqm`.
- HQM has strict byte limits for some fields. Long translated quest names or task names may be shortened.
- This tool writes translated text directly into `.hqm`; it does not use the FTB Quests or Better Questing external language-file workflow.
