import os
import hashlib
import uuid
import aiofiles
from fastapi import UploadFile

def compute_sha256_bytes(data: bytes) -> str:
    """Computes SHA-256 hex digest of in-memory bytes."""
    return hashlib.sha256(data).hexdigest()

def compute_sha256_file(file_path: str, chunk_size: int = 65536) -> str:
    """Computes SHA-256 hex digest of a file on disk in streaming chunks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_mime_from_magic(header: bytes) -> str:
    """Sniffs PDF/JPEG/PNG/TIFF from magic numbers."""
    if header.startswith(b'%PDF'):
        return 'application/pdf'
    elif header.startswith(b'\xff\xd8'):
        return 'image/jpeg'
    elif header.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    elif header.startswith(b'II*\x00') or header.startswith(b'MM\x00*'):
        return 'image/tiff'
    return 'application/octet-stream'

def validate_file_size(size: int, max_mb: int) -> bool:
    """Validates if file size in bytes is within the max_mb limit."""
    return size <= (max_mb * 1024 * 1024)

async def save_upload(
    file: UploadFile,
    upload_dir: str,
    *,
    max_size_mb: int = 25,
    allowed_mime_types: set[str] | None = None,
    stored_filename: str | None = None,
    validate_content: bool = False,
) -> tuple[str, str, int, str]:
    """
    Saves file, returns (path, mime_type, size_bytes, sha256_hash).
    Validates magic bytes and computes SHA-256 digest in a single streaming pass.
    """
    os.makedirs(upload_dir, exist_ok=True)
    
    # Only system-generated names are used on disk; never trust multipart filenames.
    safe_name = stored_filename or f"{uuid.uuid4().hex}.upload"
    if os.path.basename(safe_name) != safe_name or safe_name in {".", ".."}:
        raise ValueError("Unsafe storage filename")
    file_path = os.path.join(upload_dir, safe_name)

    # Read a complete signature prefix, then stream the upload with a hard bound.
    header = await file.read(16)
    await file.seek(0)
    
    mime_type = get_mime_from_magic(header)
    if validate_content and (mime_type == "application/octet-stream" or (allowed_mime_types and mime_type not in allowed_mime_types)):
        raise ValueError("File content is not a supported PDF or image format")
    extension = {
        "application/pdf": ".pdf",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/tiff": ".tiff",
    }.get(mime_type, ".bin")
    file_path = os.path.join(upload_dir, os.path.splitext(safe_name)[0] + extension)
    
    size_bytes = 0
    hasher = hashlib.sha256()
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):
                size_bytes += len(content)
                if size_bytes > max_size_mb * 1024 * 1024:
                    raise ValueError(f"File exceeds {max_size_mb}MB limit")
                hasher.update(content)
                await out_file.write(content)
        if validate_content and size_bytes == 0:
            raise ValueError("Empty files are not accepted")
    except Exception:
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise
            
    sha256_hash = hasher.hexdigest()
    return file_path, mime_type, size_bytes, sha256_hash
