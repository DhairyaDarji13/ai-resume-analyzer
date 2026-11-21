import re
import math
from collections import Counter

from pypdf import PdfReader
from docx import Document

SKILLS = {
    "Languages": ["python", "java", "javascript", "typescript", "c++", "c", "sql", "php", "go", "kotlin"],
    "Backend": ["flask", "django", "fastapi", "spring boot", "node.js", "express", "rest api", "graphql", "microservices"],
    "Frontend": ["html", "css", "react", "next.js", "angular", "vue", "bootstrap", "tailwind"],
    "Database": ["mysql", "postgresql", "sqlite", "mongodb", "redis", "sqlalchemy"],
    "Tools": ["git", "github", "docker", "linux", "postman", "aws", "ci/cd", "jenkins"],
    "CS Fundamentals": ["data structures", "algorithms", "oop", "dbms", "operating system", "computer networks"],
}

SECTIONS = {
    "Education": ["education", "academic"],
    "Skills": ["skills", "technical skills"],
    "Projects": ["projects", "project"],
    "Experience": ["experience", "internship", "work history"],
    "Certifications": ["certification", "certifications", "courses", "nptel"],
    "Achievements": ["achievements", "hackathon", "awards"],
}

STOPWORDS = set("""a an the and or of to in for with on at by from is are was were be as it this that
we you your our their will can must should have has had not but if than then into about over under more
experience work years year team ability strong good knowledge skills required preferred looking role job""".split())


def extract_text(path, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        reader = PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if ext == "docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    if ext == "txt":
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    raise ValueError("Unsupported file type. Upload PDF, DOCX or TXT.")


def _has(text, term):
    return re.search(r"(?<![a-z0-9+#])" + re.escape(term) + r"(?![a-z0-9+#])", text) is not None


def find_skills(text):
    low = text.lower()
    found = {}
    for cat, items in SKILLS.items():
        hits = [s for s in items if _has(low, s)]
        if hits:
            found[cat] = hits
    return found


def tokens(text):
    words = re.findall(r"[a-z][a-z0-9+#.]{1,}", text.lower())
    return [w for w in words if w not in STOPWORDS]


def cosine(a, b):
    ca, cb = Counter(a), Counter(b)
    common = set(ca) & set(cb)
    num = sum(ca[w] * cb[w] for w in common)
    den = math.sqrt(sum(v * v for v in ca.values())) * math.sqrt(sum(v * v for v in cb.values()))
    return num / den if den else 0.0


def analyze(text, job_desc=""):
    low = text.lower()
    suggestions = []

    # contact info
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    phone = re.search(r"(\+?\d[\d\s-]{8,}\d)", text)
    linkedin = "linkedin.com" in low
    github = "github.com" in low
    contact_pts = sum([bool(email), bool(phone), linkedin, github])
    contact_score = contact_pts * 2.5
    if not email: suggestions.append("Add a professional email address.")
    if not phone: suggestions.append("Add a phone number.")
    if not linkedin: suggestions.append("Add your LinkedIn profile link.")
    if not github: suggestions.append("Add your GitHub link - important for developer roles.")

    # sections
    sec_found = {name: any(_has(low, k) for k in keys) for name, keys in SECTIONS.items()}
    sec_score = sum(sec_found.values()) / len(SECTIONS) * 30
    for name, ok in sec_found.items():
        if not ok:
            suggestions.append(f"Consider adding a '{name}' section.")

    # skills
    skills = find_skills(text)
    total_skills = sum(len(v) for v in skills.values())
    skill_score = min(total_skills / 15, 1) * 30
    if total_skills < 10:
        suggestions.append("List more relevant technical skills (aim for 10+).")

    # length / quality
    words = len(text.split())
    quality_score = 0
    if 250 <= words <= 900:
        quality_score = 10
    elif words > 0:
        quality_score = 5
        suggestions.append("Keep the resume between 250 and 900 words (1 page for freshers).")
    numbers = len(re.findall(r"\d+%|\d+\+|\b\d{2,}\b", text))
    if numbers < 3:
        suggestions.append("Add measurable results (e.g. 'reduced load time by 30%').")
    verbs = ["developed", "built", "designed", "implemented", "created", "led", "optimized", "deployed"]
    if sum(_has(low, v) for v in verbs) < 3:
        suggestions.append("Start bullet points with action verbs (built, developed, implemented...).")

    # job description match
    match_pct, missing = None, []
    if job_desc.strip():
        match_pct = round(cosine(tokens(text), tokens(job_desc)) * 100 * 1.8, 1)  # scaled
        match_pct = min(match_pct, 100)
        jd_skills = find_skills(job_desc)
        resume_flat = {s for v in skills.values() for s in v}
        missing = sorted({s for v in jd_skills.values() for s in v} - resume_flat)
        if missing:
            suggestions.append("Missing skills from the job description: " + ", ".join(missing) + ".")
        score = contact_score + sec_score + skill_score * 0.7 + quality_score * 0.5 + match_pct * 0.25
        score = contact_score + sec_score * 0.8 + skill_score * 0.6 + quality_score * 0.5 + match_pct * 0.25 + 5
    else:
        score = contact_score + sec_score + skill_score + quality_score + 10 * 0.0
        score = score / 80 * 100

    score = round(max(0, min(score, 100)), 1)
    grade = "Excellent" if score >= 80 else "Good" if score >= 60 else "Needs Work"
    return {
        "score": score, "grade": grade, "words": words,
        "email": email.group(0) if email else None,
        "phone": phone.group(0).strip() if phone else None,
        "sections": sec_found, "skills": skills, "total_skills": total_skills,
        "match_pct": match_pct, "missing": missing, "suggestions": suggestions,
    }
