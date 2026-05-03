from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ✅ ADD THIS

from ml.processor import clean_text

from ml.opd.extractor import extract_opd
from ml.surgery.extractor import extract_surgery
from ml.progress.extractor import extract_progress
from ml.imaging.extractor import extract_imaging

# ✅ CREATE APP
app = FastAPI()

# ✅ ADD CORS MIDDLEWARE (RIGHT AFTER app creation)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ for now allow all (later restrict to your frontend URL)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ ROUTES
@app.post("/opd")
def opd(text: str):
    return extract_opd(clean_text(text)).dict()


@app.post("/surgery")
def surgery(text: str):
    return extract_surgery(clean_text(text)).dict()


@app.post("/progress")
def progress(text: str):
    return extract_progress(clean_text(text)).dict()


@app.post("/imaging")
def imaging(text: str):
    return extract_imaging(clean_text(text)).dict()