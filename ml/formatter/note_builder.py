from datetime import datetime

def build_opd_note(note):
    
    sep = "─" * 45
    timestamp = datetime.now().strftime("%d %b %Y  %H:%M")
    
    # Patient line
    age_str = f"Age: {note.patient.age}Y  " if note.patient.age else ""
    gender_str = f"Sex: {note.patient.gender}" if note.patient.gender else ""
    patient_line = f"{age_str}{gender_str}".strip() or "Not documented"

    # Complaints
    if note.complaints:
        duration_str = f" × {note.duration}" if note.duration else ""
        complaints_lines = "\n".join(
            f"  • {c.title()}{duration_str}" for c in note.complaints
        )
    else:
        complaints_lines = "  Not documented"

    # Negated symptoms — show separately so doctor knows they were detected
    negated_str = ""
    if note.negated_symptoms:
        negated_str = "\nDENIED SYMPTOMS\n" + "\n".join(
            f"  • {s.title()}" for s in note.negated_symptoms
        )

    # Vitals
    vitals_parts = []
    if note.vitals.bp:
        vitals_parts.append(f"BP: {note.vitals.bp}")
    if note.vitals.pulse:
        vitals_parts.append(f"Pulse: {note.vitals.pulse}")
    if note.vitals.temperature:
        vitals_parts.append(f"Temp: {note.vitals.temperature}")
    if note.vitals.spo2:
        vitals_parts.append(f"SpO2: {note.vitals.spo2}")
    if note.vitals.weight:
        vitals_parts.append(f"Wt: {note.vitals.weight}")
    vitals_str = "  " + "    ".join(vitals_parts) if vitals_parts else "  Not recorded"

    # Medications
    if note.medications:
        med_lines = "\n".join(
            f"  • {m.name.title()} {m.dose or ''}{m.unit or ''} {m.frequency or ''}".strip()
            for m in note.medications
        )
    else:
        med_lines = "  Not documented"

    # Follow up
    follow_up_str = f"Review after {note.follow_up}" if note.follow_up else "As needed"

    structured_note = f"""{sep}
OPD NOTE                          {timestamp}
{sep}
PATIENT
  {patient_line}

PRESENTING COMPLAINTS
{complaints_lines}
{negated_str}
VITALS
{vitals_str}

DIAGNOSIS
  {note.diagnosis.title() if note.diagnosis else "Not documented"}
  
⚠  AI-generated note — doctor review required
{sep}"""

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