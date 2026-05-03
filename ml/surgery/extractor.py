<<<<<<< HEAD
# ml/surgery/extractor.py
import re
from .schema import SurgeryNote
from ml.extractor.medical_extractor import MedicalExtractor
from ml.processor import split_sections

extractor = MedicalExtractor()

PROCEDURE_PATTERN = re.compile(
    r'(?:procedure|operation|surgery|performed)[:\s]+'
    r'([A-Za-z\s]+?)(?:\.|,|under|with|was)',
    re.IGNORECASE
)

SURGEON_PATTERN = re.compile(
    r'(?:surgeon|performed by|operated by|dr\.?)[:\s]+'
    r'([A-Za-z\s\.]+?)(?:\.|,|\n|assisted)',
    re.IGNORECASE
)

COMPLICATION_PATTERN = re.compile(
    r'(?:complication|complicated by|intraoperative)[:\s]+'
    r'([A-Za-z\s]+?)(?:\.|,|\n)',
    re.IGNORECASE
)

ANAESTHESIA_PATTERN = re.compile(
    r'(?:under|anaesthesia|anesthesia)[:\s]+'
    r'(general|spinal|local|epidural|regional)',
    re.IGNORECASE
)

def extract_surgery(text: str) -> SurgeryNote:
    sections = split_sections(text)
    
    # Extract procedure name
    procedure = None
    proc_match = PROCEDURE_PATTERN.search(text)
    if proc_match:
        procedure = proc_match.group(1).strip()
    
    # Extract surgeon
    surgeon = None
    surg_match = SURGEON_PATTERN.search(text)
    if surg_match:
        surgeon = surg_match.group(1).strip()
    
    # Extract anaesthesia type
    anaesthesia = None
    ana_match = ANAESTHESIA_PATTERN.search(text)
    if ana_match:
        anaesthesia = ana_match.group(1).strip()
    
    # Extract complications — check for negation
    complications = "None"
    comp_match = COMPLICATION_PATTERN.search(text)
    if comp_match:
        comp_text = comp_match.group(1).strip()
        window = text[max(0, text.lower().find(
            comp_match.group(0).lower())-30):]
        if not re.search(r'\b(no|nil|without|none)\b', 
                        window[:40], re.IGNORECASE):
            complications = comp_text
    
    # Procedure details = the procedure section text
    procedure_details = sections.get("procedure", None)
    findings = sections.get("examination", None)
    post_op = sections.get("post_op", None)
    
    # Medications from post-op section
    post_op_text = sections.get("post_op", "") + sections.get("plan", "")
    medications = extractor.extract_medications(post_op_text)
    
    return SurgeryNote(
        procedure_name=procedure,
        surgeon_name=surgeon,
        anaesthesia=anaesthesia,
        findings=findings,
        procedure_details=procedure_details,
        complications=complications,
        post_op_plan=post_op,
        medications=medications
=======
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
>>>>>>> d2423e93a7b40526def12edd5c1c05e41cfde856
    )