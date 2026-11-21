import os
import uuid
from flask import Flask, render_template, request, flash, redirect, url_for
from analyzer import extract_text, analyze

app = Flask(__name__)
app.secret_key = "change-this-secret"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED = {"pdf", "docx", "txt"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_route():
    file = request.files.get("resume")
    if not file or file.filename == "":
        flash("Please choose a resume file.")
        return redirect(url_for("index"))
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED:
        flash("Only PDF, DOCX or TXT files are allowed.")
        return redirect(url_for("index"))

    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.{ext}")
    file.save(path)
    try:
        text = extract_text(path, file.filename)
    except Exception as e:
        flash(f"Could not read file: {e}")
        return redirect(url_for("index"))
    finally:
        if os.path.exists(path):
            os.remove(path)

    if len(text.strip()) < 50:
        flash("No readable text found (scanned PDF?). Try a text-based PDF or DOCX.")
        return redirect(url_for("index"))

    result = analyze(text, request.form.get("job_desc", ""))
    return render_template("result.html", r=result, filename=file.filename)


if __name__ == "__main__":
    app.run(debug=True)
