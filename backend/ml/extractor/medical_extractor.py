import re
from ml.vocab.medical_vocab import DRUGS, DIAGNOSES, SYMPTOMS


class MedicalExtractor:

    MED_PATTERN = re.compile(
        r'([A-Za-z]+)\s+(\d+)\s*(mg|g|ml|mcg)',
        re.IGNORECASE
    )

    BP_PATTERN = re.compile(r'(\d{2,3}/\d{2,3})')
    PULSE_PATTERN = re.compile(r'pulse\s*(\d+)', re.IGNORECASE)

    NEGATION = ["no", "denies", "without", "ruled out"]

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
                    "name": name,
                    "dose": match.group(2),
                    "unit": match.group(3)
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