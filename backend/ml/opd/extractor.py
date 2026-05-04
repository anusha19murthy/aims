from .schema import OPDNote, PatientInfo, Vitals

from ml.extractor.medical_extractor import MedicalExtractor
from ml.vocab.medical_vocab import SYMPTOMS, DIAGNOSES

extractor = MedicalExtractor()

def extract_opd(text: str) -> OPDNote:

    vitals = extractor.extract_vitals(text)
    medications = extractor.extract_medications(text)

    symptoms = extractor.extract_terms(text, SYMPTOMS)
    diagnoses = extractor.extract_terms(text, DIAGNOSES)

    return OPDNote(
        patient=PatientInfo(
            name=None,
            age=None,
            gender=None
        ),
        complaints=[s["term"] for s in symptoms if not s["negated"]],
        duration=None,
        vitals=Vitals(
            temperature=None,
            bp=vitals.get("bp"),
            pulse=vitals.get("pulse")
        ),
        diagnosis=", ".join([d["term"] for d in diagnoses if not d["negated"]]),
        medications=medications,
        advice=None,
        follow_up=None
    )
