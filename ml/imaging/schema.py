from pydantic import BaseModel
<<<<<<< HEAD
from typing import Optional

class ImagingNote(BaseModel):
    patient_name: Optional[str]
    imaging_type: Optional[str]

    findings: Optional[str]
    impression: Optional[str]
    recommendation: Optional[str]
=======
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
>>>>>>> d2423e93a7b40526def12edd5c1c05e41cfde856
