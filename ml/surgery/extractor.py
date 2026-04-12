import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from .schema import SurgeryNote

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

SYSTEM_PROMPT = """You are a clinical documentation assistant.
A surgeon has just dictated an operative note.
Extract structured information from the transcript.

STRICT RULES:
- Extract ONLY what the surgeon actually said. Never invent details.
- If a field was not mentioned, return null.
- assistant_surgeon: assistant surgeon name if mentioned
- ALWAYS output in English only. Translate any Hindi or regional language words.
- Return ONLY a valid JSON object. No explanation, no markdown.

FEW-SHOT EXAMPLE:
Transcript: "Patient Arjun Singh 28 male. Emergency exploratory laparotomy for hollow viscus perforation. Surgeon Dr. Mehta. General anaesthesia. Findings: 0.5 cm perforation anterior wall duodenum, minimal soiling. Procedure: Graham patch repair, peritoneal lavage 3 litres normal saline, drain placed. Blood loss 150 ml. Post op ICU, NPO, IV Pip-Tazo, NGT continue."

Output:
{
  "patient_name": "Arjun Singh",
  "age": 28,
  "gender": "male",
  "procedure_name": "emergency exploratory laparotomy",
  "surgeon_name": "Dr. Mehta",
  "assisted_surgeon": "Dr. Kumar",
  "anaesthesia": "general anaesthesia",
  "findings": "0.5 cm perforation anterior wall duodenum, minimal peritoneal soiling, no free blood",
  "procedure_details": "Graham patch repair, peritoneal lavage with 3 litres normal saline, drain placed in right paracolic gutter",
  "blood_loss": "150 ml",
  "complications": "none",
  "post_op_plan": "ICU care, NPO, IV Piperacillin-Tazobactam, NGT continue",
  "confidence": {"procedure_name": "high", "findings": "high", "complications": "high"}
}
"""


def extract_surgery(text: str) -> SurgeryNote:
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
        return SurgeryNote(extraction_error=str(e))

    return SurgeryNote(
        patient_name=data.get("patient_name"),
        age=data.get("age"),
        gender=data.get("gender"),
        procedure_name=data.get("procedure_name"),
        surgeon_name=data.get("surgeon_name"),
        anaesthesia=data.get("anaesthesia"),
        findings=data.get("findings"),
        procedure_details=data.get("procedure_details"),
        blood_loss=data.get("blood_loss"),
        complications=data.get("complications"),
        post_op_plan=data.get("post_op_plan"),
        confidence=data.get("confidence") or {},
        extraction_error=None,
    )