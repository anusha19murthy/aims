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
    )