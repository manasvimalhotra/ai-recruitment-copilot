"""
General helper functions shared across routes/services.
"""
import json
import os
import uuid

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


def is_allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename: str) -> str:
    """Prevents overwriting files with the same name from different candidates."""
    ext = os.path.splitext(original_filename)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"


def save_upload_file(upload_dir: str, filename: str, file_bytes: bytes) -> str:
    """Saves raw bytes to disk and returns the full file path."""
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return file_path


def save_extracted_json(extracted_dir: str, candidate_id: int, profile: dict) -> str:
    """Persists a copy of the structured profile as JSON for auditing/debugging."""
    os.makedirs(extracted_dir, exist_ok=True)
    file_path = os.path.join(extracted_dir, f"candidate_{candidate_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, default=str)
    return file_path


def list_to_json(value: list) -> str:
    return json.dumps(value, default=str)


def json_to_list(value: str) -> list:
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []
