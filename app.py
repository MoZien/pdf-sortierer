import os
import re
import dropbox
from pathlib import Path
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path

# ---------------- Dropbox Setup ----------------
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

UPLOAD_FOLDER = "/uploads"
SORTED_FOLDER = "/pdf-sortiert"

CATEGORIES = ["Hochschule Material", "Verträge", "Geld und Banken", "Behörde", "Anschreiben", "Sonstiges"]

LEX = {
    "Hochschule Material": ["hochschule", "uni", "vorlesung", "übung", "klausur", "skript", "semester"],
    "Verträge": ["vertrag", "arbeitsvertrag", "mietvertrag"],
    "Geld und Banken": ["rechnung", "kontoauszug", "überweisung", "gehalt"],
    "Behörde": ["amt", "bescheid", "antrag", "jobcenter", "ausländerbehörde"],
    "Anschreiben": ["anschreiben", "bewerbung", "lebenslauf"],
}

def extract_text(local_path: str) -> str:
    text = ""
    try:
        reader = PdfReader(local_path)
        for p in reader.pages[:2]:
            t = p.extract_text()
            if t:
                text += t
    except:
        pass
    if text.strip():
        return text
    try:
        images = convert_from_path(local_path, first_page=1, last_page=1, dpi=200)
        for img in images:
            text += pytesseract.image_to_string(img, lang="deu+eng")
    except:
        pass
    return text

def classify(filename: str, text: str) -> str:
    name, body = filename.lower(), text.lower()
    for cat, terms in LEX.items():
        for t in terms:
            if t in name or t in body:
                return cat
    return "Sonstiges"

def process_new_files():
    entries = dbx.files_list_folder(UPLOAD_FOLDER).entries
    for entry in entries:
        if entry.name.endswith(".pdf"):
            local_path = f"/tmp/{entry.name}"
            dbx.files_download_to_file(local_path, entry.path_lower)
            text = extract_text(local_path)
            cat = classify(entry.name, text)
            new_path = f"{SORTED_FOLDER}/{cat}/{entry.name}"
            dbx.files_move_v2(entry.path_lower, new_path, autorename=True)
            print(f"📄 {entry.name} → {cat}")

if __name__ == "__main__":
    process_new_files()
