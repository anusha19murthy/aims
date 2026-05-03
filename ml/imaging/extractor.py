<<<<<<< HEAD
# ml/imaging/extractor.py
import re
from .schema import ImagingNote
from ml.processor import split_sections

IMAGING_TYPE_PATTERN = re.compile(
    r'\b(x.?ray|xray|ct scan|mri|ultrasound|usg|echo|'
    r'pet scan|mammogram|doppler|endoscopy|colonoscopy|'
    r'bronchoscopy|ecg|eeg|chest x.?ray|ct chest|'
    r'ct abdomen|mri brain|mri spine)\b',
    re.IGNORECASE
)

BODY_PART_PATTERN = re.compile(
    r'\b(chest|abdomen|brain|spine|pelvis|knee|shoulder|'
    r'hip|ankle|wrist|neck|thorax|lumbar|cervical|'
    r'hepatic|renal|cardiac|pulmonary)\b',
    re.IGNORECASE
)

FINDING_SIGNALS = re.compile(
    r'\b(consolidation|opacity|effusion|cardiomegaly|'
    r'fracture|lesion|mass|nodule|calcification|'
    r'hepatomegaly|splenomegaly|ascites|free fluid|'
    r'normal study|no abnormality|within normal limits|'
    r'mild|moderate|severe|bilateral|unilateral|'
    r'right|left|upper lobe|lower lobe|middle lobe)\b',
    re.IGNORECASE
)

def extract_imaging(text: str) -> ImagingNote:
    sections = split_sections(text)
    
    imaging_match = IMAGING_TYPE_PATTERN.search(text)
    imaging_type = imaging_match.group(0) if imaging_match else None
    
    body_parts = list(set(BODY_PART_PATTERN.findall(text)))
    
    findings_text = sections.get("examination") or sections.get("other")
    finding_terms = FINDING_SIGNALS.findall(text)
    
    impression = sections.get("diagnosis")
    recommendation = sections.get("plan")
    
    return ImagingNote(
        imaging_type=imaging_type,
        body_region=", ".join(body_parts) if body_parts else None,
        findings=findings_text,
        key_findings=list(set(finding_terms)) if finding_terms else [],
        impression=impression,
        recommendation=recommendation
    )
=======
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from .schema import ImagingNote

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

SYSTEM_PROMPT = """You are a clinical documentation assistant.
A radiologist or doctor is dictating an imaging report.
Extract structured information from the transcript.

STRICT RULES:
- Extract ONLY what was said. Never invent findings.
- If a field was not mentioned, return null.
- ALWAYS output in English only.
- Imaging reports do not have chief_complaint or history — leave those null.
- Capture ALL findings mentioned, organ by organ if multiple organs examined.
- Return ONLY a valid JSON object. No explanation, no markdown.

FEW-SHOT EXAMPLE:
Transcript: "Fatima Shaikh 38 female. USG abdomen pelvis. Liver normal size echotexture, no focal lesion. GB distended, multiple calculi largest 1.4 cm, wall thickening, pericholecystic fluid, CBD 4 mm. Pancreas obscured by bowel gas. Both kidneys normal. Uterus anteverted normal. No free fluid. Impression: Acute calculous cholecystitis. Surgical opinion advised."

Output:
{
  "patient_name": "Fatima Shaikh",
  "age": 38,
  "gender": "female",
  "imaging_type": "USG abdomen and pelvis",
  "clinical_indication": null,
  "findings": "Liver: normal size and echotexture, no focal lesion. Gallbladder: distended, multiple calculi largest 1.4 cm, wall thickening, pericholecystic fluid present, CBD 4 mm. Pancreas: obscured by bowel gas. Kidneys: both normal. Uterus: anteverted, normal size. No free fluid in pelvis.",
  "impression": "Acute calculous cholecystitis",
  "recommendation": "Surgical opinion advised",
  "confidence": {"findings": "high", "impression": "high"}
}
"""


def extract_imaging(text: str) -> ImagingNote:
    prompt = f"{SYSTEM_PROMPT}\n\nNow extract from this transcript:\n\"{text}\"\n\nOutput:"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)

    except Exception as e:
        return ImagingNote(extraction_error=str(e))

    return ImagingNote(
        patient_name=data.get("patient_name"),
        age=data.get("age"),
        gender=data.get("gender"),
        imaging_type=data.get("imaging_type"),
        clinical_indication=data.get("clinical_indication"),
        findings=data.get("findings"),
        impression=data.get("impression"),
        recommendation=data.get("recommendation"),
        confidence=data.get("confidence") or {},
        extraction_error=None,
    )
>>>>>>> d2423e93a7b40526def12edd5c1c05e41cfde856
