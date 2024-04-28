import os
from datetime import datetime, timezone
from flask import current_app
from werkzeug.utils import secure_filename

def utc_time_now() -> datetime:
    return datetime.now(timezone.utc)


def time_to_utc(dt):
    return dt.astimezone(timezone.utc)

def is_file_present(request):
    if "file" not in request.files:
        return None, "No file part"
    file = request.files["file"]
    if file.filename == "":
        return None, "No selected file"
    return file, None


def safely_save_file(file):

    filename = secure_filename(file.filename)
    # Use os.path.abspath to convert the path to an absolute path
    filepath = os.path.abspath(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    if not os.path.exists(os.path.dirname(filepath)):
        try:
            os.makedirs(os.path.dirname(filepath))
        except OSError as e:
            # Handle the error in case the directory cannot be created
            raise FileNotFoundError(f"Failed to create directory {os.path.dirname(filepath)}: {e}")
    try:
        file.save(filepath)
    except Exception as e:
        # Handle the error in case the file cannot be saved
        raise FileNotFoundError(f"Failed to save file {filepath}: {e}")
    
    return filepath

def validate_file_extension(file):
    file_ext = os.path.splitext(file.filename)[1]
    if not is_allowed_extension(file_ext):
        return "Invalid document type"
    return None

def check_file_size(filepath, max_size_mb):
    filesize_in_mb = os.path.getsize(filepath) / (1024 * 1024)
    if filesize_in_mb > max_size_mb:
        return False
    return filesize_in_mb


def is_allowed_extension(filename):
    ALLOWED_EXTENSIONS = current_app.config["ALLOWED_EXTENSIONS"]

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS
