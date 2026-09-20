from __future__ import annotations

from app.utils.format_utils import format_duration


def format_eta(seconds: float | None) -> str:
    return "--:--" if seconds is None else format_duration(seconds)
