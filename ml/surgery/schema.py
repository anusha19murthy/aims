from pydantic import BaseModel
from typing import Optional, Dict


class SurgeryNote(BaseModel):
    patient_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    procedure_name: Optional[str] = None
    surgeon_name: Optional[str] = None
    assistant_surgeon: Optional[str] = None
    anaesthesia: Optional[str] = None
    findings: Optional[str] = None
    procedure_details: Optional[str] = None
    blood_loss: Optional[str] = None
    complications: Optional[str] = None
    post_op_plan: Optional[str] = None
    confidence: Dict[str, str] = {}
    extraction_error: Optional[str] = None
