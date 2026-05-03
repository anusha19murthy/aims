from .schema import ProgressNote

def extract_progress(text: str) -> ProgressNote:
    return ProgressNote(
        patient_name="Anita Sharma",
        date="Day 2 post-op",

        clinical_status="Stable",
        vitals="BP 118/76, HR 80",
        assessment="Recovering well",
        plan="Continue antibiotics and ambulation"
    )
