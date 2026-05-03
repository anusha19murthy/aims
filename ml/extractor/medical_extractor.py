import re
from ml.vocab.medical_vocab import DRUGS, DIAGNOSES, SYMPTOMS


class MedicalExtractor:
    
    def extract_patient_info(self, text):
    info = {}
    
    age_match = self.AGE_PATTERN.search(text)
    if age_match:
        info["age"] = age_match.group(1)
    
    gender_match = self.GENDER_PATTERN.search(text)
    if gender_match:
        g = gender_match.group(1).lower()
        if g in ["male", "man", "boy", "m/"]:
            info["gender"] = "Male"
        else:
            info["gender"] = "Female"
    
    duration_match = self.DURATION_PATTERN.search(text)
    if duration_match:
        info["duration"] = f"{duration_match.group(1)} {duration_match.group(2)}"
    
    return info
    
    MED_PATTERN = re.compile(
        r'\b([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+'
        r'(\d+(?:\.\d+)?)\s*'
        r'(mg|mcg|g|ml|iu|units?)\s*'
        r'(?:'
            r'(od|bd|tds|qid|sos|stat|'
            r'once daily|twice daily|twice a day|'
            r'three times|thrice daily|'
            r'at night|hs|morning|evening|'
            r'before food|after food|with food)'
        r')?',
        re.IGNORECASE
    )

    BP_PATTERN = re.compile(r'(\d{2,3}/\d{2,3})')
    PULSE_PATTERN = re.compile(r'pulse\s*(\d+)', re.IGNORECASE)

    NEGATION = ["no", "denies", "without", "ruled out"]

AGE_PATTERN = re.compile(
    r'(\d{1,3})\s*(?:year|yr|y)[s\s]*(?:old|/)?',
    re.IGNORECASE
)

GENDER_PATTERN = re.compile(
    r'\b(male|female|m/|f/|boy|girl|man|woman)\b',
    re.IGNORECASE
)

DURATION_PATTERN = re.compile(
    r'(?:for|since|x)\s*(\d+)\s*(day|days|week|weeks|month|months|hour|hours)',
    re.IGNORECASE
)

SPO2_PATTERN = re.compile(
    r'(?:spo2|o2 sat|oxygen saturation)[:\s]+(\d{2,3})\s*%?',
    re.IGNORECASE
)

TEMP_PATTERN = re.compile(
    r'(?:temp|temperature)[:\s]+(\d{2,3}(?:\.\d)?)',
    re.IGNORECASE
)

WEIGHT_PATTERN = re.compile(
    r'(?:weight|wt)[:\s]+(\d{2,3}(?:\.\d)?)\s*kg',
    re.IGNORECASE
)

RR_PATTERN = re.compile(
    r'(?:rr|respiratory rate)[:\s]+(\d{2})',
    re.IGNORECASE
)
def extract_vitals(self, text):

        vitals = {}

        bp = self.BP_PATTERN.search(text)
        if bp:
            vitals["bp"] = bp.group(1)

        pulse = self.PULSE_PATTERN.search(text)
        if pulse:
            vitals["pulse"] = pulse.group(1)

        return vitals


def extract_medications(self, text):
    meds = []
    for match in self.MED_PATTERN.finditer(text):
        name = match.group(1).lower()
        if name in DRUGS:
            meds.append({
                "name": match.group(1),
                "dose": match.group(2),
                "unit": match.group(3),
                "frequency": match.group(4) if match.group(4) else "not specified"
            })
    return meds


    def extract_terms(self, text, vocab):

        found = []

        text_lower = text.lower()

        for term in vocab:

            if term in text_lower:

                negated = any(
                    neg in text_lower[max(0, text_lower.find(term)-40):text_lower.find(term)]
                    for neg in self.NEGATION
                )

                found.append({
                    "term": term,
                    "negated": negated
                })

        return found
    
    AGE_PATTERN = re.compile(
    r'(\d{1,3})\s*(?:year|yr|y)[s\s]*(?:old|/)?',
    re.IGNORECASE
)

GENDER_PATTERN = re.compile(
    r'\b(male|female|m/|f/|boy|girl|man|woman)\b',
    re.IGNORECASE
)

DURATION_PATTERN = re.compile(
    r'(?:for|since|x)\s*(\d+)\s*(day|days|week|weeks|month|months|hour|hours)',
    re.IGNORECASE
)

SPO2_PATTERN = re.compile(
    r'(?:spo2|o2 sat|oxygen saturation)[:\s]+(\d{2,3})\s*%?',
    re.IGNORECASE
)

TEMP_PATTERN = re.compile(
    r'(?:temp|temperature)[:\s]+(\d{2,3}(?:\.\d)?)',
    re.IGNORECASE
)

WEIGHT_PATTERN = re.compile(
    r'(?:weight|wt)[:\s]+(\d{2,3}(?:\.\d)?)\s*kg',
    re.IGNORECASE
)

RR_PATTERN = re.compile(
    r'(?:rr|respiratory rate)[:\s]+(\d{2})',
    re.IGNORECASE
)
    
    
    
    