from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from dotenv import load_dotenv

import os

import database
import models
import auth

from ml.processor import clean_text
from ml.opd.extractor import extract_opd
from ml.surgery.extractor import extract_surgery
from ml.progress.extractor import extract_progress
from ml.imaging.extractor import extract_imaging

# ─────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────

load_dotenv()

app = FastAPI(title="CogniScribe - AI Medical Scribe")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cogniscribe.in",
        "https://www.cogniscribe.in",
        "https://app.cogniscribe.in",
        "https://cogniscribe-web.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("APP STARTING...")

# OpenAI client — loaded lazily inside extractors, not needed at startup
try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
except Exception:
    _openai_client = None

models.Base.metadata.create_all(bind=database.engine)

# ─────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────

class TextRequest(BaseModel):
    text: str


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

class NoteCreate(BaseModel):
    note_type: str
    content: str  # JSON-encoded string of the note's fields


class PatientResponse(BaseModel):
    id: str
    name: str
    age: int | None = None
    gender: str | None = None
    contact: str | None = None

    class Config:
        from_attributes = True


class NoteResponse(BaseModel):
    id: str
    patient_id: str
    note_type: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
        
# ─────────────────────────────────────────────
# PATIENT EDIT DETAILS
# ─────────────────────────────────────────────

class PatientUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    contact: str | None = None
    
class AdminPasswordReset(BaseModel):
    email: str
    new_password: str
    admin_key: str


@app.post("/admin/reset-password")
def admin_reset_password(req: AdminPasswordReset, db: Session = Depends(database.get_db)):
    if req.admin_key != os.environ.get("ADMIN_SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Invalid admin key")

    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = auth.get_password_hash(req.new_password)
    db.commit()
    return {"message": f"Password reset for {req.email}"}

@app.patch("/patients/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: str,
    update: PatientUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.doctor_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if update.name is not None:
        patient.name = update.name
    if update.age is not None:
        patient.age = update.age
    if update.gender is not None:
        patient.gender = update.gender
    if update.contact is not None:
        patient.contact = update.contact

    db.commit()
    db.refresh(patient)
    return patient
# ─────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok"}

# ─────────────────────────────────────────────
# EXTRACTOR ROUTES
# ─────────────────────────────────────────────

@app.post("/opd")
def opd(req: TextRequest):
    try:
        result = extract_opd(clean_text(req.text))
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/surgery")
def surgery(req: TextRequest):
    try:
        result = extract_surgery(clean_text(req.text))
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/progress")
def progress(req: TextRequest):
    try:
        result = extract_progress(clean_text(req.text))
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/imaging")
def imaging(req: TextRequest):
    try:
        result = extract_imaging(clean_text(req.text))
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = auth.get_password_hash(user.password)

    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )

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
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = auth.create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }

# ─────────────────────────────────────────────
# PATIENTS (scoped to logged-in doctor)
# ─────────────────────────────────────────────

@app.get("/patients", response_model=list[PatientResponse])
def get_patients(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    return db.query(models.Patient).filter(
        models.Patient.doctor_id == current_user.id
    ).all()


@app.post("/patients", response_model=PatientResponse)
def create_patient(
    patient: PatientCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    new_patient = models.Patient(
        name=patient.name,
        age=patient.age,
        gender=patient.gender,
        contact=patient.contact,
        doctor_id=current_user.id
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient


@app.delete("/patients/{patient_id}")
def delete_patient(
    patient_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.doctor_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"ok": True}


# ─────────────────────────────────────────────
# NOTES (scoped to logged-in doctor, per patient)
# ─────────────────────────────────────────────

@app.get("/patients/{patient_id}/notes", response_model=list[NoteResponse])
def get_patient_notes(
    patient_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.doctor_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return db.query(models.Note).filter(
        models.Note.patient_id == patient_id,
        models.Note.doctor_id == current_user.id
    ).order_by(models.Note.created_at.desc()).all()


@app.post("/patients/{patient_id}/notes", response_model=NoteResponse)
def create_patient_note(
    patient_id: str,
    note: NoteCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.doctor_id == current_user.id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    new_note = models.Note(
        patient_id=patient_id,
        doctor_id=current_user.id,
        note_type=note.note_type,
        content=note.content
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.post("/auth/google")
async def google_login(req: GoogleLoginRequest, db: Session = Depends(database.get_db)):
    idinfo = auth.verify_google_token(req.token)

    if not idinfo:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = idinfo.get("email")

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        user = models.User(
            email=email,
            hashed_password=auth.get_password_hash(models.gen_uuid()),
            full_name=idinfo.get("name", "")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = auth.create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }

# ─────────────────────────────────────────────
# TRANSCRIBE
# ─────────────────────────────────────────────

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if not _openai_client:
        raise HTTPException(status_code=503, detail="OpenAI not configured")
    try:
        audio_bytes = await file.read()

        transcript = _openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=(file.filename, audio_bytes, file.content_type),
            language="en"
        )

        return {"transcript": transcript.text, "error": None}

    except Exception as e:
        return {"transcript": None, "error": str(e)}
