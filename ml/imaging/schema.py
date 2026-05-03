from pydantic import BaseModel
from typing import Optional

class ImagingNote(BaseModel):
    patient_name: Optional[str]
    imaging_type: Optional[str]

    findings: Optional[str]
    impression: Optional[str]
    recommendation: Optional[str]
