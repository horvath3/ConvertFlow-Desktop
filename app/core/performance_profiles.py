from __future__ import annotations

from dataclasses import dataclass


QUIET = "Halk / kímélő"
NORMAL = "Normál"
FAST = "Gyors"
PERFORMANCE_MODES = [QUIET, NORMAL, FAST]


@dataclass(frozen=True, slots=True)
class PerformanceProfile:
    mode: str
    ffmpeg_threads: int
    cpu_preset: str
    nvenc_preset: str
    windows_priority: str


PROFILES = {
    QUIET: PerformanceProfile(QUIET, 2, "veryfast", "p3", "idle"),
    NORMAL: PerformanceProfile(NORMAL, 0, "medium", "p5", "normal"),
    FAST: PerformanceProfile(FAST, 0, "fast", "p4", "normal"),
}


def performance_profile(mode: str) -> PerformanceProfile:
    return PROFILES.get(mode, PROFILES[NORMAL])
