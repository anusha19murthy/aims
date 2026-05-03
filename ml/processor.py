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
# ml/processor.py — add this
SECTION_PATTERNS = {
    "complaints": [
        r"complains? of|presenting with|came with|c/o|brought with|complaints?"
    ],
    "vitals": [
        r"vitals?|bp|blood pressure|temperature|pulse|spo2|weight|height"
    ],
    "examination": [
        r"on examination|o/e|per abdomen|local examination|general examination|per vaginum"
    ],
    "history": [
        r"history of|h/o|past history|family history|personal history|medical history"
    ],
    "diagnosis": [
        r"diagnosis|impression|assessment|diagnosed with|d/d|differential|a/w"
    ],
    "medications": [
        r"tab\.|cap\.|inj\.|syrup|prescribed|advised.*mg|rx"
    ],
    "plan": [
        r"plan|follow.?up|review after|referred to|advised|counselled|investigations"
    ],
    "procedure": [
        r"procedure|incision|dissection|anastomosis|closure|intraoperative|findings"
    ],
    "post_op": [
        r"post.?op|post operative|recovery|drain|wound|discharge plan"
    ]
}

def split_sections(text: str) -> dict:
    """Split dictation into clinical sections"""
    sections = {k: [] for k in SECTION_PATTERNS}
    sentences = re.split(r'[.!?]\s+|\n', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        matched = False
        for section, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    sections[section].append(sentence)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            # unclassified — add to a catch-all
            sections.setdefault("other", []).append(sentence)
    
    return {k: " ".join(v) for k, v in sections.items() if v} 