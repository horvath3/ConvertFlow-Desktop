from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from app.core.ffmpeg_manager import FFmpegManager
from app.core.models import VideoInfo

LOG = logging.getLogger(__name__)


class FFprobeManager:
    def __init__(self, ffmpeg: FFmpegManager) -> None:
        self.ffmpeg = ffmpeg

    def probe(self, path: Path) -> VideoInfo:
        if not self.ffmpeg.ffprobe_path.exists():
            raise FileNotFoundError("Az ffprobe.exe nem található. Helyezd az ffmpeg.exe és ffprobe.exe fájlokat a tools/ffmpeg mappába.")
        command = [
            str(self.ffmpeg.ffprobe_path),
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
        if result.returncode != 0:
            LOG.error("ffprobe failed: %s", result.stderr)
            raise ValueError("A videófájl nem olvasható vagy sérült.")
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), {})
        audios = [s for s in streams if s.get("codec_type") == "audio"]
        audio = audios[0] if audios else {}
        duration = float(video.get("duration") or data.get("format", {}).get("duration") or 0)
        return VideoInfo(
            path=path,
            size_bytes=path.stat().st_size,
            duration_seconds=duration,
            width=int(video.get("width") or 0),
            height=int(video.get("height") or 0),
            fps=_parse_fps(video.get("avg_frame_rate", "0/1")),
            video_codec=video.get("codec_name", "ismeretlen"),
            video_bitrate=int(video.get("bit_rate") or data.get("format", {}).get("bit_rate") or 0),
            audio_codec=audio.get("codec_name", "nincs"),
            audio_bitrate=int(audio.get("bit_rate") or 0),
            audio_streams=len(audios),
        )


def _parse_fps(value: str) -> float:
    try:
        num, den = value.split("/")
        den_f = float(den)
        return 0.0 if den_f == 0 else round(float(num) / den_f, 2)
    except (ValueError, ZeroDivisionError):
        return 0.0
