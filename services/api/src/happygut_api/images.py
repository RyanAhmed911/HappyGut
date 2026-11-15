"""Photo checks before anything leaves the backend: type, size, downscale, and EXIF/GPS strip."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class ImageRejected(ValueError):
    """The upload isn't an acceptable photo. ``code`` is shown to the client."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class CleanImage:
    data: bytes  # JPEG, no metadata
    media_type: str
    sha256: str
    width: int
    height: int


def sanitise(raw: bytes, max_bytes: int, max_side: int) -> CleanImage:
    if not raw:
        raise ImageRejected("empty_image")
    if len(raw) > max_bytes:
        raise ImageRejected("image_too_large")
    try:
        img = Image.open(io.BytesIO(raw))
        fmt = img.format
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ImageRejected("not_an_image") from None
    if fmt not in ALLOWED_FORMATS:
        raise ImageRejected("unsupported_image_type")

    img = ImageOps.exif_transpose(img)  # keep the orientation, then drop all metadata
    img = img.convert("RGB")
    img.thumbnail((max_side, max_side))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85, optimize=True)  # re-encoding writes no EXIF / GPS
    data = out.getvalue()
    return CleanImage(data, "image/jpeg", hashlib.sha256(data).hexdigest(), img.width, img.height)
