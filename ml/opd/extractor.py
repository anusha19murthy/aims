from .schema import OPDNote, PatientInfo, Vitals, Medication
from ml.extractor.medical_extractor import MedicalExtractor
from ml.vocab.medical_vocab import SYMPTOMS, DIAGNOSES
from datetime import date

extractor = MedicalExtractor()

def extract_opd(text: str) -> OPDNote:
    
    patient_info = extractor.extract_patient_info(text)
    vitals = extractor.extract_vitals(text)
    medications = extractor.extract_medications(text)
    symptoms = extractor.extract_terms(text, SYMPTOMS)
    diagnoses = extractor.extract_terms(text, DIAGNOSES)

    return OPDNote(
        date=str(date.today()),
        raw_text=text,
        patient=PatientInfo(
            name=None,
            age=patient_info.get("age"),
            gender=patient_info.get("gender")
        ),
        complaints=[s["term"] for s in symptoms if not s["negated"]],
        negated_symptoms=[s["term"] for s in symptoms if s["negated"]],
        duration=patient_info.get("duration"),
        vitals=Vitals(
            temperature=vitals.get("temperature"),
            bp=vitals.get("bp"),
            pulse=vitals.get("pulse"),
            spo2=vitals.get("spo2"),
            weight=vitals.get("weight"),
            rr=vitals.get("rr")
        ),
        diagnosis=", ".join([d["term"] for d in diagnoses if not d["negated"]]) or None,
        medications=[
            Medication(
                name=m["name"],
                dose=m["dose"],
                unit=m["unit"],
                frequency=m.get("frequency", "not specified")
            ) for m in medications
        ],
        advice=None,
        follow_up=None
    )