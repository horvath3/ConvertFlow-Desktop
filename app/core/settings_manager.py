from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class AppSettings:
    default_output_dir: str
    use_nvenc: bool = True
    default_video_codec: str = "H.264"
    default_quality_profile: str = "Jó minőség"
    default_audio_bitrate: int = 160
    open_folder_after_conversion: bool = False
    auto_remove_successful: bool = False
    parallel_jobs: int = 1
    performance_mode: str = "Normál"
    log_level: str = "INFO"
    custom_ffmpeg_dir: str = ""
    preserve_source_date: bool = False


class SettingsManager:
    def __init__(self) -> None:
        self.app_dir = Path(os.getenv("APPDATA", str(Path.home()))) / "ConvertFlow"
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.app_dir / "settings.json"
        self._settings = self._load()

    def default_settings(self) -> AppSettings:
        output_dir = Path.home() / "Videos" / "ConvertFlow"
        output_dir.mkdir(parents=True, exist_ok=True)
        return AppSettings(default_output_dir=str(output_dir))

    def _load(self) -> AppSettings:
        defaults = self.default_settings()
        if not self.settings_path.exists():
            return defaults
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            merged = asdict(defaults) | data
            if self._is_build_output_path(Path(merged["default_output_dir"])):
                merged["default_output_dir"] = defaults.default_output_dir
            return AppSettings(**merged)
        except (OSError, json.JSONDecodeError, TypeError):
            return defaults

    def _is_build_output_path(self, path: Path) -> bool:
        lowered = [part.lower() for part in path.parts]
        return "dist" in lowered or "dist_compact_ui" in lowered or "_internal" in lowered

    def get(self) -> AppSettings:
        return self._settings

    def save(self, settings: AppSettings | None = None) -> None:
        if settings is not None:
            self._settings = settings
        self.settings_path.write_text(json.dumps(asdict(self._settings), ensure_ascii=False, indent=2), encoding="utf-8")

    def reset(self) -> AppSettings:
        self._settings = self.default_settings()
        self.save()
        return self._settings
