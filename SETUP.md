# AIMS Backend — Setup & Test Guide

## 1. Get your free Gemini API key
1. Go to: https://aistudio.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Copy the key

## 2. Set the API key (do this before running)

### On Mac/Linux:
```bash
export GEMINI_API_KEY="your-key-here"
```

### On Windows (Command Prompt):
```cmd
set GEMINI_API_KEY=your-key-here
```

### Or create a .env file in the backend folder:
```
GEMINI_API_KEY=your-key-here
```

## 3. Install dependencies
```bash
pip install -r requirements.txt
```

## 4. Run the server
```bash
uvicorn app:app --reload
```

## 5. Test it — open a new terminal and run:

### Test OPD
```bash
curl -X POST http://localhost:8000/extract/opd \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Patient Ramesh Kumar 42 year male with fever and headache for 3 days. Temperature 101.4, BP 120 by 80. Diagnosed viral fever. Paracetamol 650mg twice daily. Review after 5 days."}'
```

### Test Surgery
```bash
curl -X POST http://localhost:8000/extract/surgery \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Patient Sunita Rao 55 year female. Right knee replacement by Dr. Sharma. Severe osteoarthritis found. Cemented total knee replacement done under spinal anaesthesia. No complications. Physiotherapy from day 2, review in 2 weeks."}'
```

### Test Progress Note
```bash
curl -X POST http://localhost:8000/extract/progress \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Anita Sharma day 2 post appendectomy. Patient stable, afebrile. BP 118 by 76, heart rate 80. Wound clean. Continue IV antibiotics. Review tomorrow."}'
```

### Test Imaging
```bash
curl -X POST http://localhost:8000/extract/imaging \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Rahul Verma 28 year male. Chest X-ray PA view. Right lower lobe consolidation with air bronchograms. Left lung clear. Impression: right lower lobe pneumonia. Follow up X-ray after treatment."}'
```

## What good output looks like

For OPD you should get back JSON like:
```json
{
  "patient": {"name": "Ramesh Kumar", "age": 42, "gender": "male"},
  "chief_complaint": "fever and headache",
  "duration": "3 days",
  "vitals": {"temperature": "101.4", "bp": "120/80", "pulse": null},
  "diagnosis": "viral fever",
  "medications": [{"name": "paracetamol", "dose": "650mg", "frequency": "twice daily"}],
  "follow_up": "5 days",
  "confidence": {"diagnosis": "high", "medications": "high"},
  "extraction_error": null
}
```

## What to tell your UI developer

The UI should:
1. POST transcript to /extract/{type}
2. Display each field in its own box
3. If confidence for a field is "low" → show that field with yellow background
4. If extraction_error is not null → show a red warning banner
5. When doctor edits a field → POST to /correction with old and new value
