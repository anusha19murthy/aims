from fastapi import FastAPI

from ml.processor import clean_text

from ml.opd.extractor import extract_opd
from ml.surgery.extractor import extract_surgery
from ml.progress.extractor import extract_progress
from ml.imaging.extractor import extract_imaging

app = FastAPI()


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