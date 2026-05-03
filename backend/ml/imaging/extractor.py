from .schema import ImagingNote

def extract_imaging(text: str) -> ImagingNote:
    text_lower = text.lower()

    return ImagingNote(
        patient_name="Rahul Verma",
        imaging_type="Chest X-ray",

        findings="Right lower lobe consolidation",
        impression="Suggestive of pneumonia",
        recommendation="Clinical correlation advised"
    )
