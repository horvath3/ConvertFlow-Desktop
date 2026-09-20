from __future__ import annotations

import os
import shutil
from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv", ".m4v", ".mpeg", ".mpg", ".flv", ".ts", ".mts", ".m2ts"}


def is_supported_video(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    index = 2
    while True:
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def default_output_name(input_path: Path, suffix: str, extension: str) -> str:
    return f"{input_path.stem}_{suffix}.{extension.lstrip('.')}"


def is_writable_directory(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return os.access(path, os.W_OK)
    except OSError:
        return False


def has_free_space(path: Path, required_bytes: int) -> bool:
    return shutil.disk_usage(path).free >= required_bytes
