import os
import hashlib
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

async def save_upload(file: UploadFile, upload_dir: str) -> tuple[str, str, int, str]:
    """
    Saves file, returns (path, mime_type, size_bytes, sha256_hash).
    Validates magic bytes and computes SHA-256 digest in a single streaming pass.
    """
    os.makedirs(upload_dir, exist_ok=True)
    
    # Read first 10 bytes for magic number
    header = await file.read(10)
    await file.seek(0)
    
    mime_type = get_mime_from_magic(header)
    
    file_path = os.path.join(upload_dir, file.filename or "uploaded_file")
    
    size_bytes = 0
    hasher = hashlib.sha256()
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024 * 1024):  # Read 1MB chunks
            size_bytes += len(content)
            hasher.update(content)
            await out_file.write(content)
            
    sha256_hash = hasher.hexdigest()
    return file_path, mime_type, size_bytes, sha256_hash
