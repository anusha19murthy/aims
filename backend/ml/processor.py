import re

def clean_text(text: str) -> str:
    text = text.lower()

    replacements = {
        "one zero one point four": "101.4",
        "one zero one": "101",
        "one twenty over eighty": "120/80",
        "one twenty by eighty": "120/80",
        "beats per minute": "bpm"
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    text = re.sub(r"\s+", " ", text).strip()
    return text
