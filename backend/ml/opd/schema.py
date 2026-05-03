from pydantic import BaseModel
from typing import List, Optional

class PatientInfo(BaseModel):
    name: Optional[str]
    age: Optional[int]
    gender: Optional[str]

class Vitals(BaseModel):
    temperature: Optional[str]
    bp: Optional[str]
    pulse: Optional[str]

class Medication(BaseModel):
    name: str
    dose: Optional[str]
    frequency: Optional[str]

class OPDNote(BaseModel):
    patient: PatientInfo
    complaints: List[str]
    duration: Optional[str]
    vitals: Vitals
    diagnosis: Optional[str]
    medications: List[Medication]
    advice: Optional[str]
    follow_up: Optional[str]
