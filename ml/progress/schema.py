from pydantic import BaseModel
<<<<<<< HEAD
from typing import Optional

class ProgressNote(BaseModel):
    patient_name: Optional[str]
    date: Optional[str]

    clinical_status: Optional[str]
    vitals: Optional[str]
    assessment: Optional[str]
    plan: Optional[str]
=======
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
>>>>>>> d2423e93a7b40526def12edd5c1c05e41cfde856
