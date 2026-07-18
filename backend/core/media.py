"""Раздача MEDIA с поддержкой HTTP Range (нужно для перемотки видео)."""

from __future__ import annotations

import mimetypes
import posixpath
import re
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.utils._os import safe_join
from django.views.static import was_modified_since

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


def serve_media_with_range(request, path: str):
    """
    Аналог django.views.static.serve, но с 206 Partial Content.
    Без Range браузер не может нормально мотать большие mp4.
    """
    path = posixpath.normpath(path).lstrip("/")
    fullpath = Path(safe_join(settings.MEDIA_ROOT, path))
    if not fullpath.exists() or not fullpath.is_file():
        raise Http404(f"Файл не найден: {path}")

    stat = fullpath.stat()
    if not was_modified_since(request.META.get("HTTP_IF_MODIFIED_SINCE"), stat.st_mtime):
        return HttpResponse(status=304)

    content_type, _encoding = mimetypes.guess_type(str(fullpath))
    content_type = content_type or "application/octet-stream"
    file_size = stat.st_size
    range_header = request.META.get("HTTP_RANGE", "").strip()

    if not range_header:
        response = FileResponse(fullpath.open("rb"), content_type=content_type)
        response["Accept-Ranges"] = "bytes"
        response["Content-Length"] = str(file_size)
        return response

    match = RANGE_RE.fullmatch(range_header)
    if not match:
        response = HttpResponse(status=416)
        response["Content-Range"] = f"bytes */{file_size}"
        return response

    start_s, end_s = match.groups()
    try:
        start = int(start_s) if start_s else 0
        end = int(end_s) if end_s else file_size - 1
    except ValueError:
        response = HttpResponse(status=416)
        response["Content-Range"] = f"bytes */{file_size}"
        return response

    if end_s == "" and start_s:
        # bytes=N- → до конца файла
        end = file_size - 1
    if start_s == "" and end_s:
        # bytes=-N → последние N байт
        length = int(end_s)
        if length <= 0:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{file_size}"
            return response
        start = max(file_size - length, 0)
        end = file_size - 1

    if start >= file_size or end >= file_size or start > end:
        response = HttpResponse(status=416)
        response["Content-Range"] = f"bytes */{file_size}"
        return response

    length = end - start + 1
    fh = fullpath.open("rb")
    fh.seek(start)

    response = FileResponse(
        _LimitedReader(fh, length),
        status=206,
        content_type=content_type,
    )
    response["Accept-Ranges"] = "bytes"
    response["Content-Length"] = str(length)
    response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
    return response


class _LimitedReader:
    """Читает не больше `remaining` байт из файлового объекта."""

    def __init__(self, fileobj, remaining: int, block_size: int = 8192):
        self.fileobj = fileobj
        self.remaining = remaining
        self.block_size = block_size

    def read(self, size: int = -1) -> bytes:
        if self.remaining <= 0:
            return b""
        if size is None or size < 0:
            size = self.block_size
        size = min(size, self.remaining, self.block_size)
        data = self.fileobj.read(size)
        self.remaining -= len(data)
        return data

    def close(self) -> None:
        self.fileobj.close()

    def seekable(self) -> bool:
        return False
