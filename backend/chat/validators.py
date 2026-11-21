from pathlib import Path
from zipfile import ZipFile, BadZipFile

from PIL import Image
from rest_framework.exceptions import ValidationError


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".pdf", ".doc", ".docx", ".txt",
    ".mp4",
}


def validate_attachment_file(uploaded_file):

    # 1. Validate file size
    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValidationError(
            "File size cannot exceed 10 MB."
        )

    # 2. Validate extension
    extension = Path(uploaded_file.name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            "This file type is not supported."
        )

    # 3. Validate actual file content
    try:
        if extension in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
            uploaded_file.seek(0)

            image = Image.open(uploaded_file)
            image.verify()

            if image.format.lower() not in {
                "jpeg", "png", "gif", "webp"
            }:
                raise ValidationError("Invalid image format.")

        elif extension == ".pdf":
            uploaded_file.seek(0)

            if uploaded_file.read(5) != b"%PDF-":
                raise ValidationError("Invalid PDF file.")

        elif extension == ".doc":
            uploaded_file.seek(0)

            if uploaded_file.read(8) != bytes.fromhex(
                "D0CF11E0A1B11AE1"
            ):
                raise ValidationError("Invalid DOC file.")

        elif extension == ".docx":
            uploaded_file.seek(0)

            with ZipFile(uploaded_file) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise ValidationError("Invalid DOCX file.")

        elif extension == ".txt":
            uploaded_file.seek(0)
            uploaded_file.read().decode("utf-8")

        elif extension == ".mp4":
            uploaded_file.seek(4)

            if uploaded_file.read(4) != b"ftyp":
                raise ValidationError("Invalid MP4 file.")

    except ValidationError:
        raise

    except Exception:
        raise ValidationError(
            "The uploaded file is corrupted or invalid."
        )

    finally:
        uploaded_file.seek(0)

    return uploaded_file