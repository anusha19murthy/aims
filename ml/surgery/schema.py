from pydantic import BaseModel
from typing import Optional

class SurgeryNote(BaseModel):
    patient_name: Optional[str]
    procedure_name: Optional[str]
    surgeon_name: Optional[str]

    findings: Optional[str]
    procedure_details: Optional[str]
    complications: Optional[str]

    post_op_plan: Optional[str]
