from __future__ import annotations

from pathlib import Path

import pytest

from app.core.ffmpeg_manager import FFmpegManager
from app.core.models import ConversionOptions, ConversionTask, VideoInfo
from app.core.performance_profiles import QUIET, performance_profile
from app.core.target_size_calculator import calculate_video_bitrate, target_size_to_bytes
from app.core.video_profiles import quality_args
from app.utils.file_utils import default_output_name, ensure_unique_path
from app.utils.format_utils import format_duration, format_file_size


def test_target_size_calculation() -> None:
    result = calculate_video_bitrate(100, target_size_to_bytes(100, "MB"), 160)
    assert result.total_bitrate_kbps > 8000
    assert result.video_bitrate_kbps == result.total_bitrate_kbps - result.audio_bitrate_kbps - result.safety_margin_kbps


def test_target_size_too_small() -> None:
    with pytest.raises(ValueError):
        calculate_video_bitrate(3600, target_size_to_bytes(1, "MB"), 320)


def test_format_file_size() -> None:
    assert format_file_size(1024 * 1024) == "1.0 MB"


def test_format_duration() -> None:
    assert format_duration(65) == "01:05"
    assert format_duration(3661) == "01:01:01"


def test_output_filename_generation(tmp_path: Path) -> None:
    source = tmp_path / "árvíztűrő video.mkv"
    assert default_output_name(source, "compressed", "mp4") == "árvíztűrő video_compressed.mp4"
    existing = tmp_path / "video_compressed.mp4"
    existing.write_text("", encoding="utf-8")
    assert ensure_unique_path(existing).name == "video_compressed_2.mp4"


def test_profile_ffmpeg_args() -> None:
    args = quality_args("H.264", "Jó minőség")
    assert args.codec == "libx264"
    assert "-crf" in args.args


def test_quiet_profile_uses_lighter_ffmpeg_args() -> None:
    profile = performance_profile(QUIET)
    assert profile.ffmpeg_threads == 2
    args = quality_args("H.264", "Jó minőség", performance_mode=QUIET)
    assert "veryfast" in args.args


def test_ffmpeg_path_detection() -> None:
    manager = FFmpegManager()
    assert manager.ffmpeg_path.name == "ffmpeg.exe"
    assert manager.ffprobe_path.name == "ffprobe.exe"


def test_quiet_mode_adds_thread_limit_to_command() -> None:
    manager = FFmpegManager()
    options = ConversionOptions(performance_mode=QUIET)
    task = ConversionTask(VideoInfo(Path("input.mp4"), 1000, duration_seconds=60), Path("output.mp4"), options)
    command = manager.build_command(task)
    assert "-threads" in command
    assert command[command.index("-threads") + 1] == "2"
