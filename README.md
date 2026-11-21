# AI Resume Analyzer (Flask)

Upload a resume (PDF/DOCX/TXT) and get an ATS-style score, detected skills/sections,
job-description match percentage, and improvement suggestions.

## Run
```
python -m venv venv
venv\Scripts\activate        (Windows)   |   source venv/bin/activate (Linux/Mac)
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## How it works
- Text extraction: pypdf (PDF), python-docx (DOCX)
- Skill and section detection: keyword/regex matching
- Job match: cosine similarity over word-frequency vectors
- Score = contact info (10) + sections (30) + skills (30) + quality (10), scaled to 100
