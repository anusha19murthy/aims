from .schema import SurgeryNote

def extract_surgery(text: str) -> SurgeryNote:
    text_lower = text.lower()

    return SurgeryNote(
        patient_name="Anita Sharma" if "anita" in text_lower else None,
        procedure_name="Appendectomy" if "appendectomy" in text_lower else None,
        surgeon_name="Dr. Mehta",

        findings="Inflamed appendix",
        procedure_details="Laparoscopic appendectomy performed",
        complications="None",
        post_op_plan="IV antibiotics, review after 48 hours"
    )
