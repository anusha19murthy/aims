from pydantic import BaseModel
from typing import List, Optional

class PatientInfo(BaseModel):
    name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None

class Vitals(BaseModel):
    temperature: Optional[str] = None
    bp: Optional[str] = None
    pulse: Optional[str] = None
    spo2: Optional[str] = None
    weight: Optional[str] = None
    rr: Optional[str] = None

class Medication(BaseModel):
    name: str
    dose: Optional[str] = None
    unit: Optional[str] = None
    frequency: Optional[str] = None

class OPDNote(BaseModel):
    date: Optional[str] = None
    raw_text: str
    patient: PatientInfo
    complaints: List[str] = []
    negated_symptoms: List[str] = []
    duration: Optional[str] = None
    vitals: Vitals
    diagnosis: Optional[str] = None
    medications: List[Medication] = []
    advice: Optional[str] = None
    follow_up: Optional[str] = None