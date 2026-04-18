import hashlib
from pathlib import Path
from uuid import uuid4

from app.settings import STORAGE_ROOT


STORAGE_ROOT.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(filename: str, content: bytes) -> tuple[str, str]:
    checksum = hashlib.sha256(content).hexdigest()
    suffix = Path(filename).suffix
    storage_key = f"{uuid4().hex}{suffix}"
    destination = STORAGE_ROOT / storage_key
    destination.write_bytes(content)
    return storage_key, checksum
