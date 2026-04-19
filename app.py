import os
import json
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status, Request, Response
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

class GoogleLoginRequest(BaseModel):
    token: str

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
async def login(request: Request, db: Session = Depends(database.get_db)):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
    else:
        form_data = await request.form()
        email = form_data.get("username")
        password = form_data.get("password")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "full_name": user.full_name}}

@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.post("/auth/google")
async def google_login(req: GoogleLoginRequest, db: Session = Depends(database.get_db)):
    idinfo = auth.verify_google_token(req.token)
    if not idinfo:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    email = idinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google token does not contain email")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        name = idinfo.get("name", "")
        # Give them an unusable random password since they login via google
        random_password = auth.get_password_hash(models.gen_uuid())
        user = models.User(email=email, hashed_password=random_password, full_name=name)
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "full_name": user.full_name}}

# ── Patients ──────────────────────────────────────────────────────────────────

@app.post("/patients")
def create_patient(patient: PatientCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    new_patient = models.Patient(**patient.dict(), doctor_id=current_user.id)
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

@app.get("/patients")
def read_patients(response: Response, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    patients = db.query(models.Patient).filter(models.Patient.doctor_id == current_user.id).all()
    return patients

@app.get("/patients/{patient_id}/notes")
def read_patient_notes(patient_id: str, response: Response, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id, models.Patient.doctor_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or unauthorized")
    notes = db.query(models.Note).filter(models.Note.patient_id == patient_id).order_by(models.Note.created_at.desc()).all()
    result = []
    for n in notes:
        try:
            content = json.loads(n.content) if n.content else {}
        except:
            content = {}
        result.append({
            "id": n.id,
            "note_type": n.note_type,
            "created_at": n.created_at,
            "content": content
        })
    return result


# ── Transcription ─────────────────────────────────────────────────────────────

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user)):
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
def opd(req: TranscriptRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    note_data = extract_opd(req.transcript)
    if req.patient_id:
        new_note = models.Note(
            patient_id=req.patient_id,
            doctor_id=current_user.id,
            note_type="opd",
            content=json.dumps(note_data.dict())
        )
        db.add(new_note)
        db.commit()
    return note_data.dict()


@app.post("/extract/surgery")
def surgery(req: TranscriptRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    note_data = extract_surgery(req.transcript)
    if req.patient_id:
        new_note = models.Note(
            patient_id=req.patient_id,
            doctor_id=current_user.id,
            note_type="surgery",
            content=json.dumps(note_data.dict())
        )
        db.add(new_note)
        db.commit()
    return note_data.dict()


@app.post("/extract/progress")
def progress(req: TranscriptRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    note_data = extract_progress(req.transcript)
    if req.patient_id:
        new_note = models.Note(
            patient_id=req.patient_id,
            doctor_id=current_user.id,
            note_type="progress",
            content=json.dumps(note_data.dict())
        )
        db.add(new_note)
        db.commit()
    return note_data.dict()


@app.post("/extract/imaging")
def imaging(req: TranscriptRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    note_data = extract_imaging(req.transcript)
    if req.patient_id:
        new_note = models.Note(
            patient_id=req.patient_id,
            doctor_id=current_user.id,
            note_type="imaging",
            content=json.dumps(note_data.dict())
        )
        db.add(new_note)
        db.commit()
    return note_data.dict()


# ── Correction logging ────────────────────────────────────────────────────────

@app.post("/correction")
def log_correction(req: CorrectionRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    req_dict = req.dict()
    if req_dict.get("doctor_id") is None:
        req_dict["doctor_id"] = current_user.id
    new_corr = models.Correction(**req_dict)
    db.add(new_corr)
    db.commit()
    return {"status": "logged"}


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0-llm"}