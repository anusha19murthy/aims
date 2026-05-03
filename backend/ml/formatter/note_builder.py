def build_opd_note(note):
    complaints = ", ".join(note.complaints) if note.complaints else "symptoms"
    duration = f'for {note.duration} days' if note.duration else ""
    subjective = f"patient complains of {complaints}{duration}."
    vitals = []

    if note.vitals.temperature:
        vitals.append(f"Temperature: {note.vitals.temperature}") 
    if note.vitals.bp:
        vitals.append(f"BP: {note.vitals.bp}")
    if note.vitals.pulse:
        vitals.append(f"Pulse: {note.vitals.pulse}")

    objective = "\n".join(vitals) if vitals else "No vitals recorded"
    meds = []

    for m in note.medications:
        meds.append(f"{m.name} {m.dose} {m.frequency}")

    medication_text = "\n".join(meds) if meds else "No medications prescribed"
    plan = medication_text

    if note.follow_up:
        plan += f"\nFollow up after {note.follow_up} days"

    structured_note = f"""
SUBJECTIVE
{subjective}

OBJECTIVE
{objective}

ASSESSMENT
{note.diagnosis or "Not specified"}

PLAN
{plan}
"""
    return structured_note.strip()

def build_surgery_note(note):
    structured_note = f"""
PATIENT
{note.patient_name or "Unknown"}
PROCEDURE
{note.procedure_name or "Not Specified"}
SURGEON
{note.surgeon_name or "Not Speciified"}
FINDINGS
{note.findings or "None"}
PROCEDURE DETAILS
{note.procedure_details or "Not documneted"}
COMPLICATIONS
{note.complications or "None"}
POST OPERATIVE PLAN
{note.post_op_plan or "Not Specified"}
"""
    return structured_note.strip()

def build_progress_note(note):
    structured_note = f"""
PATIENT
{note.patient_name or "Unknown"}
DATE
{note.date or "Not Specified"}
CLINICAL STATUS
{note.clinical_status or "Not Specified"}
VITALS
{note.vitals or "Not recorded"}
ASSESSMENT
{note.assessment or "Not Specified"}
PLAN
{note.plan or "Not Specified"}
"""
    return structured_note.strip()

def build_imaging_note(note):
    structured_note = f"""
PATIENT
{note.patient_name or "Unknown"}
IMAGING TYPE
{note.imaging_type or "Not Specified"}
FINDINGS
{note.findings or "None"}
IMPRESSION
{note.impression or "Not Specified"}
RECOMMENDATION
{note.recommendation or "None"}
"""
    return structured_note.strip()