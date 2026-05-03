from pydantic import BaseModel
<<<<<<< HEAD
from typing import List, Optional

class PatientInfo(BaseModel):
    name: Optional[str] = None
    age: Optional[str] = None
=======
from typing import List, Optional, Dict

class PatientInfo(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
>>>>>>> d2423e93a7b40526def12edd5c1c05e41cfde856
    gender: Optional[str] = None

class Vitals(BaseModel):
    temperature: Optional[str] = None
    bp: Optional[str] = None
    pulse: Optional[str] = None
    spo2: Optional[str] = None
<<<<<<< HEAD
    weight: Optional[str] = None
    rr: Optional[str] = None
=======
>>>>>>> d2423e93a7b40526def12edd5c1c05e41cfde856

class Medication(BaseModel):
    name: str
    dose: Optional[str] = None
<<<<<<< HEAD
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
=======
    frequency: Optional[str] = None

class OPDNote(BaseModel):
    patient: PatientInfo
    chief_complaint: Optional[str] = None
    duration: Optional[str] = None
    history: Optional[str] = None
    examination_findings: Optional[str] = None
    vitals: Vitals
    ecg_findings: Optional[str] = None
    investigation_results: Optional[str] = None
    diagnosis: Optional[str] = None
    medications: List[Medication] = []
    advice: Optional[str] = None
    follow_up: Optional[str] = None
    confidence: Dict[str, str] = {}
    extraction_error: Optional[str] = None
>>>>>>> d2423e93a7b40526def12edd5c1c05e41cfde856
