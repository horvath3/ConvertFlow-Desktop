from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from app.core.models import CompressionMode, ConversionMode, ConversionOptions, ConversionTask, VideoInfo
from app.core.performance_profiles import performance_profile
from app.core.target_size_calculator import calculate_video_bitrate, target_size_to_bytes
from app.core.video_profiles import CODEC_TO_FFMPEG, NVENC_CODECS, quality_args

LOG = logging.getLogger(__name__)


class FFmpegManager:
    def __init__(self, custom_dir: str = "") -> None:
        self.custom_dir = Path(custom_dir) if custom_dir else None

    @property
    def bundled_dir(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent / "tools" / "ffmpeg"
        return Path.cwd() / "tools" / "ffmpeg"

    def executable(self, name: str) -> Path:
        filename = f"{name}.exe" if not name.endswith(".exe") else name
        if self.custom_dir:
            candidate = self.custom_dir / filename
            if candidate.exists():
                return candidate
        return self.bundled_dir / filename

    @property
    def ffmpeg_path(self) -> Path:
        return self.executable("ffmpeg")

    @property
    def ffprobe_path(self) -> Path:
        return self.executable("ffprobe")

    def is_available(self) -> bool:
        return self.ffmpeg_path.exists() and self.ffprobe_path.exists()

    def version(self) -> str:
        if not self.ffmpeg_path.exists():
            return "Nem található"
        try:
            result = subprocess.run([str(self.ffmpeg_path), "-version"], capture_output=True, text=True, timeout=10, check=False)
            return result.stdout.splitlines()[0] if result.stdout else "Ismeretlen"
        except (OSError, subprocess.SubprocessError) as exc:
            LOG.exception("FFmpeg version check failed")
            return str(exc)

    def available_nvenc_encoders(self) -> set[str]:
        if not self.ffmpeg_path.exists():
            return set()
        try:
            result = subprocess.run([str(self.ffmpeg_path), "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=20, check=False)
            output = result.stdout + result.stderr
            found = {encoder for encoder in NVENC_CODECS.values() if encoder in output}
            LOG.info("NVENC encoders: %s", sorted(found))
            return found
        except (OSError, subprocess.SubprocessError):
            LOG.exception("NVENC detection failed")
            return set()

    def encoder_for(self, options: ConversionOptions, nvenc_available: set[str]) -> str:
        if options.use_nvenc and options.video_codec in NVENC_CODECS and NVENC_CODECS[options.video_codec] in nvenc_available:
            return NVENC_CODECS[options.video_codec]
        return CODEC_TO_FFMPEG[options.video_codec]

    def build_command(self, task: ConversionTask, pass_number: int | None = None, passlog: Path | None = None, nvenc_available: set[str] | None = None) -> list[str]:
        nvenc_available = nvenc_available or set()
        options = task.options
        args = [str(self.ffmpeg_path), "-hide_banner", "-y", "-i", str(task.input_info.path)]
        perf = performance_profile(options.performance_mode)
        if perf.ffmpeg_threads > 0:
            args.extend(["-threads", str(perf.ffmpeg_threads)])
        args.extend(self._video_args(task.input_info, options, pass_number, passlog, nvenc_available))
        args.extend(self._audio_args(options, pass_number))
        if options.keep_subtitles and pass_number is None:
            args.extend(["-map", "0", "-map_metadata", "0" if options.keep_metadata else "-1"])
            if not options.keep_audio_tracks:
                args.extend(["-map", "0:v:0", "-map", "0:a:0?"])
        elif not options.keep_metadata:
            args.extend(["-map_metadata", "-1"])
        args.extend(["-progress", "pipe:1", "-nostats"])
        if pass_number == 1:
            args.append("NUL")
        else:
            args.append(str(task.output_path))
        LOG.info("Generated FFmpeg command: %s", args)
        return args

    def needs_two_pass(self, options: ConversionOptions) -> bool:
        return options.mode == ConversionMode.COMPRESS and options.compression_mode == CompressionMode.TARGET_SIZE and not options.use_nvenc and options.video_codec in {"H.264", "H.265 / HEVC"}

    def _video_args(self, info: VideoInfo, options: ConversionOptions, pass_number: int | None, passlog: Path | None, nvenc_available: set[str]) -> list[str]:
        encoder = self.encoder_for(options, nvenc_available)
        args = ["-c:v", encoder]
        if options.mode == ConversionMode.COMPRESS and options.compression_mode == CompressionMode.TARGET_SIZE:
            result = calculate_video_bitrate(info.duration_seconds, target_size_to_bytes(options.target_size_value, options.target_size_unit), options.audio_bitrate_kbps)
            encoder_uses_nvenc = encoder in NVENC_CODECS.values()
            preset = performance_profile(options.performance_mode).nvenc_preset if encoder_uses_nvenc else performance_profile(options.performance_mode).cpu_preset
            args.extend(["-preset", preset, "-b:v", f"{result.video_bitrate_kbps}k"])
            if pass_number:
                args.extend(["-pass", str(pass_number), "-passlogfile", str(passlog)])
        elif options.mode == ConversionMode.COMPRESS and options.compression_mode == CompressionMode.BITRATE:
            args.extend(["-b:v", f"{options.video_bitrate_kbps}k", "-maxrate", f"{options.max_bitrate_kbps}k", "-bufsize", f"{options.buffer_size_kbps}k"])
        else:
            args.extend(quality_args(options.video_codec, options.quality_profile, options.use_nvenc and encoder in NVENC_CODECS.values(), options.performance_mode).args)
        filters = []
        if options.resolution != "Eredeti":
            width = int(options.resolution.split("×")[0].strip())
            filters.append(f"scale='min({width},iw)':-2")
        if filters:
            args.extend(["-vf", ",".join(filters)])
        if options.fps != "Eredeti":
            args.extend(["-r", options.fps])
        return args

    def _audio_args(self, options: ConversionOptions, pass_number: int | None) -> list[str]:
        if pass_number == 1:
            return ["-an"]
        if options.audio_mode == "Hang eltávolítása":
            return ["-an"]
        if options.audio_mode == "Eredeti hangsáv másolása":
            return ["-c:a", "copy"]
        codec = {"AAC": "aac", "MP3": "libmp3lame", "Opus": "libopus"}.get(options.audio_mode, "aac")
        return ["-c:a", codec, "-b:a", f"{options.audio_bitrate_kbps}k"]
