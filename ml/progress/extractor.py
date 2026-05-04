import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from .schema import ProgressNote

load_dotenv()

try:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
except Exception:
    client = None

SYSTEM_PROMPT = """You are a clinical documentation assistant.
A doctor is doing ward rounds and dictating a progress note for a hospital patient.
Extract structured information from the transcript.

STRICT RULES:
- Extract ONLY what was said. Never invent clinical details.
- If a field was not mentioned, return null.
- ALWAYS output in English only. Translate any Hindi or regional language words.
- If diagnosis is not stated but inferable, include it with confidence "medium".
- For ICU patients, capture ventilator settings separately.
- Always capture urine output if mentioned in the vitals field.
- Return ONLY a valid JSON object. No explanation, no markdown.

FIELDS TO EXTRACT:
- patient_name
- day: post-op day or ICU day if mentioned
- clinical_status: overall status (stable, critical, improving, etc.)
- vitals: BP, pulse, temperature, SpO2, urine output as a single string
- ventilator_settings: FiO2, PEEP, tidal volume if on ventilator
- investigation_results: labs, cultures, trends
- examination_findings: what was found on examination
- assessment: diagnosis or clinical assessment
- plan: management plan
- follow_up: review date if mentioned
- confidence: {"clinical_status": "high/medium", "plan": "high/medium"}

FEW-SHOT EXAMPLE:
Transcript: "Kavitha day 5 post LSCS. Afebrile. BP 124 over 82, pulse 80, SpO2 99. Uterus well contracted, lochia normal, wound healthy. Haemoglobin today 9.8, starting oral iron. Plan discharge tomorrow. Tab Ferrous Sulphate twice daily, Tab Calcium for 6 weeks."

Output:
{
  "patient_name": "Kavitha",
  "day": "day 5 post LSCS",
  "clinical_status": "stable, afebrile",
  "vitals": "BP 124/82, pulse 80, SpO2 99%",
  "ventilator_settings": null,
  "investigation_results": "haemoglobin 9.8 g/dL",
  "examination_findings": "uterus well contracted, lochia normal, wound healthy",
  "assessment": "recovering well post LSCS, mild anaemia",
  "plan": "start oral iron, discharge tomorrow",
  "follow_up": "7 days for suture removal",
  "confidence": {"clinical_status": "high", "vitals": "high", "plan": "high"}
}
"""


def extract_progress(text: str) -> ProgressNote:
    if not client:
        return ProgressNote(extraction_error="OpenAI client not configured")

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
        return ProgressNote(extraction_error=str(e))

    return ProgressNote(
        patient_name=data.get("patient_name"),
        day=data.get("day"),
        clinical_status=data.get("clinical_status"),
        vitals=data.get("vitals"),
        ventilator_settings=data.get("ventilator_settings"),
        investigation_results=data.get("investigation_results"),
        examination_findings=data.get("examination_findings"),
        assessment=data.get("assessment"),
        plan=data.get("plan"),
        follow_up=data.get("follow_up"),
        confidence=data.get("confidence") or {},
        extraction_error=None,
    )
