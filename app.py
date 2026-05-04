from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
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
    allow_origins=["*"],
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
