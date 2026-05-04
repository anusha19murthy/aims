from pydantic import BaseModel
from typing import Optional, Dict


class ProgressNote(BaseModel):
    patient_name: Optional[str] = None
    day: Optional[str] = None
    clinical_status: Optional[str] = None
    vitals: Optional[str] = None
    ventilator_settings: Optional[str] = None
    investigation_results: Optional[str] = None
    examination_findings: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    follow_up: Optional[str] = None
    confidence: Dict[str, str] = {}
    extraction_error: Optional[str] = None
