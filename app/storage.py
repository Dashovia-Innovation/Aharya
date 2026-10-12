"""Report file storage. Local disk for now; swap for Supabase Storage in production."""

import shutil
from pathlib import Path

from app.config import settings

EXTENSIONS = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}


def sniff_media_type(data: bytes) -> str | None:
    """Identify the file from its magic bytes; the client's content-type is not trusted."""
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None


def save(assessment_id: str, kind: str, media_type: str, data: bytes) -> str:
    folder = settings.upload_dir / assessment_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{kind}{EXTENSIONS[media_type]}"
    path.write_bytes(data)
    return str(path)


def read(path: str) -> bytes:
    return Path(path).read_bytes()


def delete_assessment(assessment_id: str) -> None:
    shutil.rmtree(settings.upload_dir / assessment_id, ignore_errors=True)
