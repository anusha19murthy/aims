import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from .schema import OPDNote, PatientInfo, Vitals, Medication

load_dotenv()
try:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
except Exception:
    client = None

SYSTEM_PROMPT = """You are a clinical documentation assistant for Indian doctors.
A doctor has just finished an OPD consultation and dictated notes.
Extract structured information from the transcript.

STRICT RULES:
- Extract ONLY what the doctor actually said. Never invent or guess.
- If a field was not mentioned, return null.
- ALWAYS output in English only. Translate any Hindi, Hinglish, or regional language words to English.
- If diagnosis is not explicitly stated but can be clearly inferred, include it with confidence marked as "medium".
- For medications, include all drugs explicitly named including Indian brand names.
- Return ONLY a valid JSON object. No explanation, no markdown, no extra text.

FIELDS TO EXTRACT:
- patient: name, age, gender
- chief_complaint: main reason for visit in English
- duration: how long the complaint has been present
- history: relevant past history, associated symptoms, negatives
- examination_findings: what doctor found on examination
- vitals: temperature, bp, pulse, spo2
- ecg_findings: any ECG findings mentioned
- investigation_results: any lab results, blood tests, imaging results mentioned
- diagnosis: final diagnosis or impression
- medications: list of drugs with name, dose, frequency
- advice: non-medication advice given
- follow_up: when to return
- confidence: {"diagnosis": "high/medium/low", "medications": "high/medium/low"}

FEW-SHOT EXAMPLE:
Transcript: "Patient hai Mrs. Sunita Devi 34 year female, pet mein dard 3-4 din se. BP 110 over 70, pulse 82. Abdomen soft, mild tenderness. IBS ya gastritis. Tab Pan 40 morning empty stomach, Meftal Spas SOS."

Output:
{
  "patient": {"name": "Mrs. Sunita Devi", "age": 34, "gender": "female"},
  "chief_complaint": "abdominal pain",
  "duration": "3-4 days",
  "history": null,
  "examination_findings": "abdomen soft, mild periumbilical tenderness",
  "vitals": {"temperature": null, "bp": "110/70", "pulse": "82", "spo2": null},
  "ecg_findings": null,
  "investigation_results": null,
  "diagnosis": "IBS or gastritis",
  "medications": [
    {"name": "Pan", "dose": "40mg", "frequency": "morning empty stomach"},
    {"name": "Meftal Spas", "dose": null, "frequency": "SOS for pain"}
  ],
  "advice": null,
  "follow_up": null,
  "confidence": {"diagnosis": "medium", "medications": "high"}
}
"""


def extract_opd(text: str) -> OPDNote:
    if not client:
        return _empty_opd_note(error="OpenAI client not configured")

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

    except json.JSONDecodeError:
        return _empty_opd_note(error="LLM returned invalid JSON")
    except Exception as e:
        return _empty_opd_note(error=str(e))

    patient_data = data.get("patient") or {}
    vitals_data = data.get("vitals") or {}
    meds_data = data.get("medications") or []
    confidence = {
        k: v for k, v in (data.get("confidence") or {}).items()
        if v and v != "null"
    }

    return OPDNote(
        patient=PatientInfo(
            name=patient_data.get("name"),
            age=patient_data.get("age"),
            gender=patient_data.get("gender"),
        ),
        chief_complaint=data.get("chief_complaint"),
        duration=data.get("duration"),
        history=data.get("history"),
        examination_findings=data.get("examination_findings"),
        vitals=Vitals(
            temperature=vitals_data.get("temperature"),
            bp=vitals_data.get("bp"),
            pulse=vitals_data.get("pulse"),
            spo2=vitals_data.get("spo2"),
        ),
        ecg_findings=data.get("ecg_findings"),
        investigation_results=data.get("investigation_results"),
        diagnosis=data.get("diagnosis"),
        medications=[
            Medication(
                name=m.get("name", ""),
                dose=m.get("dose"),
                frequency=m.get("frequency"),
            )
            for m in meds_data
            if m.get("name")
        ],
        advice=data.get("advice"),
        follow_up=data.get("follow_up"),
        confidence=confidence,
        extraction_error=None,
    )


def _empty_opd_note(error: str) -> OPDNote:
    return OPDNote(
        patient=PatientInfo(name=None, age=None, gender=None),
        chief_complaint=None,
        duration=None,
        history=None,
        examination_findings=None,
        vitals=Vitals(temperature=None, bp=None, pulse=None, spo2=None),
        ecg_findings=None,
        investigation_results=None,
        diagnosis=None,
        medications=[],
        advice=None,
        follow_up=None,
        confidence={},
        extraction_error=error,
    )
