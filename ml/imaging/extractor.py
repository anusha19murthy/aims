import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from .schema import ImagingNote

load_dotenv()

try:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
except Exception:
    client = None

SYSTEM_PROMPT = """You are a clinical documentation assistant.
A radiologist or doctor is dictating an imaging report.
Extract structured information from the transcript.

STRICT RULES:
- Extract ONLY what was said. Never invent findings.
- If a field was not mentioned, return null.
- ALWAYS output in English only.
- Capture ALL findings mentioned, organ by organ if multiple organs examined.
- Return ONLY a valid JSON object. No explanation, no markdown.

FIELDS TO EXTRACT:
- patient_name, age, gender
- imaging_type: type of scan/study (USG, CT, MRI, X-ray, etc.)
- clinical_indication: reason for the study if mentioned
- findings: detailed findings organ by organ
- impression: radiologist's impression/conclusion
- recommendation: any follow-up or further imaging recommended
- confidence: {"findings": "high/medium", "impression": "high/medium"}

FEW-SHOT EXAMPLE:
Transcript: "Fatima Shaikh 38 female. USG abdomen pelvis. Liver normal size echotexture, no focal lesion. GB distended, multiple calculi largest 1.4 cm, wall thickening, pericholecystic fluid, CBD 4 mm. Both kidneys normal. No free fluid. Impression: Acute calculous cholecystitis. Surgical opinion advised."

Output:
{
  "patient_name": "Fatima Shaikh",
  "age": 38,
  "gender": "female",
  "imaging_type": "USG abdomen and pelvis",
  "clinical_indication": null,
  "findings": "Liver: normal size and echotexture, no focal lesion. Gallbladder: distended, multiple calculi largest 1.4 cm, wall thickening, pericholecystic fluid. CBD 4 mm. Kidneys: both normal. No free fluid.",
  "impression": "Acute calculous cholecystitis",
  "recommendation": "Surgical opinion advised",
  "confidence": {"findings": "high", "impression": "high"}
}
"""


def extract_imaging(text: str) -> ImagingNote:
    if not client:
        return ImagingNote(extraction_error="OpenAI client not configured")

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
