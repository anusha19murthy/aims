import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

from ml.opd.extractor import extract_opd
from ml.surgery.extractor import extract_surgery
from ml.progress.extractor import extract_progress
from ml.imaging.extractor import extract_imaging

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

app = FastAPI(title="CogniScribe - AI Medical Scribe")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ────────────────────────────────────────────────────────────

class TranscriptRequest(BaseModel):
    transcript: str
    patient_id: str | None = None


class CorrectionRequest(BaseModel):
    note_id: str
    note_type: str
    field_name: str
    original_value: str | None
    corrected_value: str
    doctor_id: str | None = None


# ── Transcription ─────────────────────────────────────────────────────────────

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """
    Step 1 of pipeline.
    UI sends audio file → returns English transcript.
    Works for all Indian languages and dialects — Hindi, Marathi,
    Kannada, Tamil, Telugu, Gujarati, Bengali, Punjabi, Malayalam,
    Odia, Urdu, and any Hinglish or regional language mix.
    """
    try:
        audio_bytes = await file.read()

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=(file.filename, audio_bytes, file.content_type),
            language="en",
            prompt="Medical consultation dictation in India. Doctor may speak English, Hindi, Odia, Marathi, Kannada, Tamil or a regional language mix. Common Indian drug names: Paracetamol, Dolo, Crocin, Cetirizine, Cheston Cold, Metformin, Glimepiride, Pregabalin, Telmisartan, Amlodipine, Azithromycin, Pantoprazole, Pan, Clopidogrel, Aspirin, Atorvastatin, Escitalopram, Prednisolone, Augmentin, Combiflam, Meftal, Ondansetron, Ramipril, Metoprolol, Furosemide, Warfarin, Alteplase, Tiotropium, Salbutamol, Montelukast, Losartan, Clonazepam, Alprazolam, Amoxicillin, Ciprofloxacin, Cefazolin, Meropenem, Piperacillin, Vancomycin, Insulin, Levothyroxine, Atorvastatin, Rosuvastatin. Medical terms: hypertension, diabetes, tachycardia, bradycardia, dyspnoea, haemoptysis, haematemesis, syncope, palpitations, myocardial infarction, appendicitis, cholecystitis, pneumonia, COPD, asthma, stroke, seizure, sepsis, anaemia."
        )

        return {
            "transcript": transcript.text,
            "error": None
        }

    except Exception as e:
        return {
            "transcript": None,
            "error": str(e)
        }


# ── Note extraction ───────────────────────────────────────────────────────────

@app.post("/extract/opd")
def opd(req: TranscriptRequest):
    note = extract_opd(req.transcript)
    return note.dict()


@app.post("/extract/surgery")
def surgery(req: TranscriptRequest):
    note = extract_surgery(req.transcript)
    return note.dict()


@app.post("/extract/progress")
def progress(req: TranscriptRequest):
    note = extract_progress(req.transcript)
    return note.dict()


@app.post("/extract/imaging")
def imaging(req: TranscriptRequest):
    note = extract_imaging(req.transcript)
    return note.dict()


# ── Correction logging ────────────────────────────────────────────────────────

corrections_log = []  # TODO: replace with PostgreSQL later

@app.post("/correction")
def log_correction(req: CorrectionRequest):
    corrections_log.append(req.dict())
    return {"status": "logged"}


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0-llm"}