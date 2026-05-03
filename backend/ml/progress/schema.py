from pydantic import BaseModel
from typing import Optional

class ProgressNote(BaseModel):
    patient_name: Optional[str]
    date: Optional[str]

    clinical_status: Optional[str]
    vitals: Optional[str]
    assessment: Optional[str]
    plan: Optional[str]
