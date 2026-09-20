from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TargetSizeResult:
    total_bitrate_kbps: int
    video_bitrate_kbps: int
    audio_bitrate_kbps: int
    safety_margin_kbps: int
    expected_size_bytes: int
    warning: str = ""


def target_size_to_bytes(value: float, unit: str) -> int:
    multiplier = 1024**3 if unit.upper() == "GB" else 1024**2
    return int(value * multiplier)


def calculate_video_bitrate(duration_seconds: float, target_bytes: int, audio_bitrate_kbps: int, overhead_ratio: float = 0.02) -> TargetSizeResult:
    if duration_seconds <= 0:
        raise ValueError("A videó hossza nem ismert.")
    total_kbps = int((target_bytes * 8) / duration_seconds / 1000)
    safety = max(1, int(total_kbps * overhead_ratio))
    video_kbps = total_kbps - audio_bitrate_kbps - safety
    if video_kbps <= 0:
        raise ValueError("A célméret túl kicsi: a számított videó bitráta nulla vagy negatív.")
    warning = "A megadott célméret mellett a videó minősége nagyon gyenge lehet." if video_kbps < 500 else ""
    return TargetSizeResult(total_kbps, video_kbps, audio_bitrate_kbps, safety, target_bytes, warning)
