from pydantic import BaseModel
from typing import Optional, Dict


class ImagingNote(BaseModel):
    patient_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    imaging_type: Optional[str] = None
    clinical_indication: Optional[str] = None
    findings: Optional[str] = None
    impression: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: Dict[str, str] = {}
    extraction_error: Optional[str] = None
