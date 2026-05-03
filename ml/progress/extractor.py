# ml/progress/extractor.py
import re
from .schema import ProgressNote
from ml.extractor.medical_extractor import MedicalExtractor
from ml.processor import split_sections

extractor = MedicalExtractor()

DELTA_PATTERN = re.compile(
    r'\b(improving|improved|worsening|worsened|stable|'
    r'deteriorating|comfortable|restless|afebrile|febrile|'
    r'ambulant|ambulating|tolerating)\b',
    re.IGNORECASE
)

DAY_PATTERN = re.compile(
    r'(?:day|pod|post.?op\s*day)\s*(\d+)', re.IGNORECASE)

def extract_progress(text: str) -> ProgressNote:
    sections = split_sections(text)
    vitals = extractor.extract_vitals(text)
    medications = extractor.extract_medications(text)
    
    # Clinical status — look for delta language
    status_matches = DELTA_PATTERN.findall(text)
    clinical_status = ", ".join(set(status_matches)) if status_matches else None
    
    # Post-op day
    day_match = DAY_PATTERN.search(text)
    post_op_day = f"Day {day_match.group(1)}" if day_match else None
    
    return ProgressNote(
        post_op_day=post_op_day,
        clinical_status=clinical_status,
        vitals=vitals,
        assessment=sections.get("diagnosis"),
        plan=sections.get("plan"),
        medications=medications
    )