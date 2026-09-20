from __future__ import annotations

from dataclasses import dataclass

from app.core.ffmpeg_manager import FFmpegManager


@dataclass(frozen=True, slots=True)
class HardwareStatus:
    h264_nvenc: bool
    hevc_nvenc: bool
    av1_nvenc: bool

    @property
    def any_nvenc(self) -> bool:
        return self.h264_nvenc or self.hevc_nvenc or self.av1_nvenc


def detect_hardware(ffmpeg: FFmpegManager) -> HardwareStatus:
    encoders = ffmpeg.available_nvenc_encoders()
    return HardwareStatus("h264_nvenc" in encoders, "hevc_nvenc" in encoders, "av1_nvenc" in encoders)
