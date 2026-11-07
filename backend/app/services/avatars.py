"""Small, defensive storage helpers for user-uploaded avatar images."""

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from backend.app.core.config import get_settings

MAX_AVATAR_BYTES = 3 * 1024 * 1024
_MEDIA_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class AvatarValidationError(ValueError):
    """A user-correctable upload error with a safe message."""


def avatar_directory() -> Path:
    """Return the owned directory; settings may point at a non-repository runtime volume."""
    return get_settings().avatar_upload_dir


def _matches_declared_image_type(content: bytes, media_type: str) -> bool:
    if media_type == "image/jpeg":
        return len(content) >= 4 and content.startswith(b"\xff\xd8\xff") and content.endswith(b"\xff\xd9")
    if media_type == "image/png":
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            return False
        cursor = 8
        saw_header = saw_end = False
        while cursor + 12 <= len(content):
            chunk_length = int.from_bytes(content[cursor:cursor + 4], "big")
            chunk_type = content[cursor + 4:cursor + 8]
            next_cursor = cursor + 12 + chunk_length
            if next_cursor > len(content):
                return False
            if chunk_type == b"IHDR":
                saw_header = chunk_length == 13 and cursor == 8
            if chunk_type == b"IEND":
                saw_end = chunk_length == 0 and next_cursor == len(content)
                return saw_header and saw_end
            cursor = next_cursor
        return False
    if media_type == "image/webp":
        return (
            len(content) >= 16
            and content[:4] == b"RIFF"
            and content[8:12] == b"WEBP"
            and int.from_bytes(content[4:8], "little") + 8 == len(content)
        )
    return False


async def save_avatar(upload: UploadFile) -> str:
    """Validate and persist a bounded raster image under a generated filename only."""
    media_type = (upload.content_type or "").lower()
    extension = _MEDIA_TYPES.get(media_type)
    if not extension:
        raise AvatarValidationError("Choose a JPEG, PNG, or WEBP image.")

    content = await upload.read(MAX_AVATAR_BYTES + 1)
    if not content:
        raise AvatarValidationError("Choose a non-empty image file.")
    if len(content) > MAX_AVATAR_BYTES:
        raise AvatarValidationError("Avatar images must be 3 MB or smaller.")
    if not _matches_declared_image_type(content, media_type):
        raise AvatarValidationError("The uploaded file is not a valid declared image type.")

    directory = avatar_directory()
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    (directory / filename).write_bytes(content)
    return filename


def delete_avatar(filename: str | None) -> None:
    """Delete only a generated file in the owned avatar directory, if it remains present."""
    if not filename or Path(filename).name != filename:
        return
    candidate = avatar_directory() / filename
    if candidate.is_file():
        candidate.unlink()
