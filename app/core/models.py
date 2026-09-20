from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4


class TaskStatus(str, Enum):
    WAITING = "Várakozik"
    PREPARING = "Előkészítés"
    PASS1 = "Első menet"
    PASS2 = "Második menet"
    CONVERTING = "Konvertálás"
    PAUSED = "Szüneteltetve"
    DONE = "Kész"
    CANCELED = "Megszakítva"
    FAILED = "Sikertelen"


class ConversionMode(str, Enum):
    CONVERT = "convert"
    COMPRESS = "compress"


class CompressionMode(str, Enum):
    QUALITY = "quality"
    TARGET_SIZE = "target_size"
    BITRATE = "bitrate"


@dataclass(slots=True)
class VideoInfo:
    path: Path
    size_bytes: int
    duration_seconds: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    video_codec: str = "ismeretlen"
    video_bitrate: int = 0
    audio_codec: str = "nincs"
    audio_bitrate: int = 0
    audio_streams: int = 0


@dataclass(slots=True)
class ConversionOptions:
    mode: ConversionMode = ConversionMode.CONVERT
    container: str = "mp4"
    video_codec: str = "H.264"
    audio_mode: str = "AAC"
    audio_bitrate_kbps: int = 160
    quality_profile: str = "Jó minőség"
    resolution: str = "Eredeti"
    fps: str = "Eredeti"
    keep_metadata: bool = True
    keep_subtitles: bool = True
    keep_audio_tracks: bool = True
    preserve_source_date: bool = False
    use_nvenc: bool = False
    performance_mode: str = "Normál"
    compression_mode: CompressionMode = CompressionMode.QUALITY
    target_size_value: float = 500.0
    target_size_unit: str = "MB"
    video_bitrate_kbps: int = 2500
    max_bitrate_kbps: int = 4000
    buffer_size_kbps: int = 8000


@dataclass(slots=True)
class ConversionTask:
    input_info: VideoInfo
    output_path: Path
    options: ConversionOptions
    id: str = field(default_factory=lambda: uuid4().hex)
    status: TaskStatus = TaskStatus.WAITING
    progress: float = 0.0
    speed: str = ""
    elapsed_seconds: float = 0.0
    eta_seconds: float | None = None
    ffmpeg_status: str = ""
    error: str = ""
    technical_error: str = ""
