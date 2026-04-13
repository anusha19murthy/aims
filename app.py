import os
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

import database
import models
import auth

from ml.opd.extractor import extract_opd
from ml.surgery.extractor import extract_surgery
from ml.progress.extractor import extract_progress
from ml.imaging.extractor import extract_imaging
print("APP STARTING...")
load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

models.Base.metadata.create_all(bind=database.engine)

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

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str

class PatientCreate(BaseModel):
    name: str
    age: int | None = None
    gender: str | None = None
    contact: str | None = None

# ── Authentication ────────────────────────────────────────────────────────────

@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password, full_name=user.full_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "full_name": user.full_name}}

@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# ── Patients ──────────────────────────────────────────────────────────────────

@app.post("/patients")
def create_patient(patient: PatientCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    new_patient = models.Patient(**patient.dict(), doctor_id=current_user.id)
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

@app.get("/patients")
def read_patients(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    patients = db.query(models.Patient).filter(models.Patient.doctor_id == current_user.id).all()
    return patients


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

@app.post("/correction")
def log_correction(req: CorrectionRequest, db: Session = Depends(database.get_db)):
    new_corr = models.Correction(**req.dict())
    db.add(new_corr)
    db.commit()
    return {"status": "logged"}


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0-llm"}