import os
import json
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

import database
import auth

from ml.opd.extractor import extract_opd
from ml.surgery.extractor import extract_surgery
from ml.progress.extractor import extract_progress
from ml.imaging.extractor import extract_imaging
print("APP STARTING...")
load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


app = FastAPI(title="CogniScribe - AI Medical Scribe")

@app.on_event("startup")
def initialise_database():
    database.ensure_indexes()

def public_user(user): return {"id": user["id"], "email": user["email"], "full_name": user["full_name"]}
def public_patient(patient): return {key: value for key, value in patient.items() if key != "_id"}

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
    reason: str | None = None
    appointment_date: str | None = None

class PatientUpdate(PatientCreate):
    pass

class NoteCreate(BaseModel):
    note_type: str
    content: dict

# ── Authentication ────────────────────────────────────────────────────────────

@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate):
    db = database.get_database()
    if db.users.find_one({"email": user.email.lower()}):
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = {"id": str(uuid4()), "email": user.email.lower(), "hashed_password": auth.get_password_hash(user.password), "full_name": user.full_name, "created_at": datetime.now(timezone.utc)}
    db.users.insert_one(new_user)
    return public_user(new_user)

@app.post("/login")
async def login(request: Request):
    db = database.get_database()
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
    else:
        form_data = await request.form()
        email = form_data.get("username")
        password = form_data.get("password")

    user = db.users.find_one({"email": (email or "").lower()})
    if not user or not auth.verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": public_user(user)}

@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: dict = Depends(auth.get_current_user)):
    return public_user(current_user)

@app.post("/auth/google")
async def google_login(req: GoogleLoginRequest):
    db = database.get_database()
    idinfo = auth.verify_google_token(req.token)
    if not idinfo:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    email = idinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google token does not contain email")
    
    user = db.users.find_one({"email": email.lower()})
    if not user:
        name = idinfo.get("name", "")
        # Give them an unusable random password since they login via google
        user = {"id": str(uuid4()), "email": email.lower(), "hashed_password": auth.get_password_hash(str(uuid4())), "full_name": name, "created_at": datetime.now(timezone.utc)}
        db.users.insert_one(user)

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": public_user(user)}

# ── Patients ──────────────────────────────────────────────────────────────────

@app.post("/patients")
def create_patient(patient: PatientCreate, current_user: dict = Depends(auth.get_current_user)):
    new_patient = {"id": str(uuid4()), **patient.dict(), "doctor_id": current_user["id"], "created_at": datetime.now(timezone.utc)}
    database.get_database().patients.insert_one(new_patient)
    return public_patient(new_patient)

@app.get("/patients")
def read_patients(response: Response, current_user: dict = Depends(auth.get_current_user)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return [public_patient(item) for item in database.get_database().patients.find({"doctor_id": current_user["id"]}).sort("created_at", -1)]

@app.put("/patients/{patient_id}")
def update_patient(patient_id: str, update: PatientUpdate, current_user: dict = Depends(auth.get_current_user)):
    result = database.get_database().patients.update_one({"id": patient_id, "doctor_id": current_user["id"]}, {"$set": update.dict()})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Patient not found or unauthorized")
    return public_patient(database.get_database().patients.find_one({"id": patient_id}))

@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: str, current_user: dict = Depends(auth.get_current_user)):
    db = database.get_database()
    result = db.patients.delete_one({"id": patient_id, "doctor_id": current_user["id"]})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Patient not found or unauthorized")
    db.notes.delete_many({"patient_id": patient_id})
    return {"status": "deleted"}

@app.get("/patients/{patient_id}/notes")
def read_patient_notes(patient_id: str, response: Response, current_user: dict = Depends(auth.get_current_user)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    db = database.get_database()
    if not db.patients.find_one({"id": patient_id, "doctor_id": current_user["id"]}):
        raise HTTPException(status_code=404, detail="Patient not found or unauthorized")
    return [{"id": item["id"], "note_type": item["note_type"], "created_at": item["created_at"], "content": item["content"]} for item in db.notes.find({"patient_id": patient_id}).sort("created_at", -1)]

@app.post("/patients/{patient_id}/notes")
def create_note(patient_id: str, note: NoteCreate, current_user: dict = Depends(auth.get_current_user)):
    db = database.get_database()
    if not db.patients.find_one({"id": patient_id, "doctor_id": current_user["id"]}):
        raise HTTPException(status_code=404, detail="Patient not found or unauthorized")
    new_note = {"id": str(uuid4()), "patient_id": patient_id, "doctor_id": current_user["id"], "note_type": note.note_type, "content": note.content, "created_at": datetime.now(timezone.utc)}
    db.notes.insert_one(new_note)
    return {"id": new_note["id"], "note_type": new_note["note_type"], "created_at": new_note["created_at"], "content": note.content}


# ── Transcription ─────────────────────────────────────────────────────────────

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), current_user: dict = Depends(auth.get_current_user)):
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
def opd(req: TranscriptRequest, current_user: dict = Depends(auth.get_current_user)):
    note_data = extract_opd(req.transcript)
    if req.patient_id:
        database.get_database().notes.insert_one({"id": str(uuid4()), "patient_id": req.patient_id, "doctor_id": current_user["id"], "note_type": "opd", "content": note_data.dict(), "created_at": datetime.now(timezone.utc)})
    return note_data.dict()


@app.post("/extract/surgery")
def surgery(req: TranscriptRequest, current_user: dict = Depends(auth.get_current_user)):
    note_data = extract_surgery(req.transcript)
    if req.patient_id:
        database.get_database().notes.insert_one({"id": str(uuid4()), "patient_id": req.patient_id, "doctor_id": current_user["id"], "note_type": "surgery", "content": note_data.dict(), "created_at": datetime.now(timezone.utc)})
    return note_data.dict()


@app.post("/extract/progress")
def progress(req: TranscriptRequest, current_user: dict = Depends(auth.get_current_user)):
    note_data = extract_progress(req.transcript)
    if req.patient_id:
        database.get_database().notes.insert_one({"id": str(uuid4()), "patient_id": req.patient_id, "doctor_id": current_user["id"], "note_type": "progress", "content": note_data.dict(), "created_at": datetime.now(timezone.utc)})
    return note_data.dict()


@app.post("/extract/imaging")
def imaging(req: TranscriptRequest, current_user: dict = Depends(auth.get_current_user)):
    note_data = extract_imaging(req.transcript)
    if req.patient_id:
        database.get_database().notes.insert_one({"id": str(uuid4()), "patient_id": req.patient_id, "doctor_id": current_user["id"], "note_type": "imaging", "content": note_data.dict(), "created_at": datetime.now(timezone.utc)})
    return note_data.dict()


# ── Correction logging ────────────────────────────────────────────────────────

@app.post("/correction")
def log_correction(req: CorrectionRequest, current_user: dict = Depends(auth.get_current_user)):
    req_dict = req.dict()
    if req_dict.get("doctor_id") is None:
        req_dict["doctor_id"] = current_user["id"]
    req_dict.update({"id": str(uuid4()), "created_at": datetime.now(timezone.utc)})
    database.get_database().corrections.insert_one(req_dict)
    return {"status": "logged"}


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0-llm"}
