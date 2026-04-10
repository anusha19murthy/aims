import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from .schema import ProgressNote

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

SYSTEM_PROMPT = """You are a clinical documentation assistant.
A doctor is doing ward rounds and dictating a progress note for a hospital patient.
Extract structured information from the transcript.

STRICT RULES:
- Extract ONLY what was said. Never invent clinical details.
- If a field was not mentioned, return null.
- ALWAYS output in English only. Translate any Hindi or regional language words.
- If diagnosis is not stated but inferable, include it with confidence "medium".
- For ICU patients, capture ventilator settings separately.
- Always capture urine output if mentioned — include it in vitals field alongside BP and pulse.
- Capture all lab values and investigation results in investigation_results field including culture reports, sensitivity pending status, and trend values like "creatinine risen from 1.8 to 3.2".
- Return ONLY a valid JSON object. No explanation, no markdown.

FEW-SHOT EXAMPLE 1 (post-op ward patient):
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
  "plan": "start oral iron, discharge tomorrow, suture removal after 7 days",
  "follow_up": "7 days for suture removal",
  "confidence": {"clinical_status": "high", "vitals": "high", "plan": "high"}
}

FEW-SHOT EXAMPLE 2 (ICU patient):
Transcript: "Mohan Lal day 3 ICU ARDS secondary to pneumonia. Ventilated FiO2 60%, PEEP 8, tidal volume 400. Temp 38.4, BP 92 over 60 on Noradrenaline 0.1 mcg per kg per min, pulse 110. Procalcitonin 18. Plan increase PEEP to 10, prone positioning, add Polymyxin B, family counselled prognosis poor."

Output:
{
  "patient_name": "Mohan Lal",
  "day": "day 3 ICU",
  "clinical_status": "critical, ventilated, on vasopressor support",
  "vitals": "temp 38.4, BP 92/60, pulse 110, on Noradrenaline 0.1 mcg/kg/min",
  "ventilator_settings": "FiO2 60%, PEEP 8, tidal volume 400ml",
  "investigation_results": "procalcitonin 18",
  "examination_findings": null,
  "assessment": "ARDS secondary to severe pneumonia, day 3 ICU, worsening",
  "plan": "increase PEEP to 10, prone positioning, add Polymyxin B for MDR coverage, monitor renal function",
  "follow_up": null,
  "confidence": {"clinical_status": "high", "vitals": "high", "plan": "high"}
}
"""


def extract_progress(text: str) -> ProgressNote:
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