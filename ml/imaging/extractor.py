# ml/imaging/extractor.py
import re
from .schema import ImagingNote
from ml.processor import split_sections

IMAGING_TYPE_PATTERN = re.compile(
    r'\b(x.?ray|xray|ct scan|mri|ultrasound|usg|echo|'
    r'pet scan|mammogram|doppler|endoscopy|colonoscopy|'
    r'bronchoscopy|ecg|eeg|chest x.?ray|ct chest|'
    r'ct abdomen|mri brain|mri spine)\b',
    re.IGNORECASE
)

BODY_PART_PATTERN = re.compile(
    r'\b(chest|abdomen|brain|spine|pelvis|knee|shoulder|'
    r'hip|ankle|wrist|neck|thorax|lumbar|cervical|'
    r'hepatic|renal|cardiac|pulmonary)\b',
    re.IGNORECASE
)

FINDING_SIGNALS = re.compile(
    r'\b(consolidation|opacity|effusion|cardiomegaly|'
    r'fracture|lesion|mass|nodule|calcification|'
    r'hepatomegaly|splenomegaly|ascites|free fluid|'
    r'normal study|no abnormality|within normal limits|'
    r'mild|moderate|severe|bilateral|unilateral|'
    r'right|left|upper lobe|lower lobe|middle lobe)\b',
    re.IGNORECASE
)

def extract_imaging(text: str) -> ImagingNote:
    sections = split_sections(text)
    
    imaging_match = IMAGING_TYPE_PATTERN.search(text)
    imaging_type = imaging_match.group(0) if imaging_match else None
    
    body_parts = list(set(BODY_PART_PATTERN.findall(text)))
    
    findings_text = sections.get("examination") or sections.get("other")
    finding_terms = FINDING_SIGNALS.findall(text)
    
    impression = sections.get("diagnosis")
    recommendation = sections.get("plan")
    
    return ImagingNote(
        imaging_type=imaging_type,
        body_region=", ".join(body_parts) if body_parts else None,
        findings=findings_text,
        key_findings=list(set(finding_terms)) if finding_terms else [],
        impression=impression,
        recommendation=recommendation
    )
