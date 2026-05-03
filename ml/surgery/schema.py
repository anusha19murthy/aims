from pydantic import BaseModel
<<<<<<< HEAD
from typing import Optional

class SurgeryNote(BaseModel):
    patient_name: Optional[str]
    procedure_name: Optional[str]
    surgeon_name: Optional[str]

    findings: Optional[str]
    procedure_details: Optional[str]
    complications: Optional[str]

    post_op_plan: Optional[str]
=======
from typing import Optional, Dict

class SurgeryNote(BaseModel):
    patient_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    procedure_name: Optional[str] = None
    surgeon_name: Optional[str] = None
    assistant_surgeon: str | None = None
    anaesthesia: Optional[str] = None
    findings: Optional[str] = None
    procedure_details: Optional[str] = None
    blood_loss: Optional[str] = None
    complications: Optional[str] = None
    post_op_plan: Optional[str] = None
    confidence: Dict[str, str] = {}
    extraction_error: Optional[str] = None
>>>>>>> d2423e93a7b40526def12edd5c1c05e41cfde856
