from __future__ import annotations

import logging
import sys
import shutil
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal

from app.core.ffmpeg_manager import FFmpegManager
from app.core.models import ConversionTask, TaskStatus
from app.core.performance_profiles import performance_profile
from app.utils.file_utils import has_free_space, is_writable_directory

LOG = logging.getLogger(__name__)


class ConversionWorker(QObject):
    task_updated = Signal(object)
    task_finished = Signal(object)

    def __init__(self, ffmpeg: FFmpegManager, task: ConversionTask, nvenc_available: set[str]) -> None:
        super().__init__()
        self.ffmpeg = ffmpeg
        self.task = task
        self.nvenc_available = nvenc_available
        self.process: QProcess | None = None
        self.started_at = 0.0
        self._eta: float | None = None
        self._passlog_dir: tempfile.TemporaryDirectory[str] | None = None
        self._current_pass: int | None = None

    def start(self) -> None:
        try:
            self._preflight()
            self.started_at = time.monotonic()
            if self.ffmpeg.needs_two_pass(self.task.options):
                self._passlog_dir = tempfile.TemporaryDirectory(prefix="convertflow_pass_")
                self._run_pass(1)
            else:
                self._run_pass(None)
        except Exception as exc:
            LOG.exception("Conversion start failed")
            self._fail("A konvertálás nem indítható el.", str(exc))

    def cancel(self) -> None:
        self.task.status = TaskStatus.CANCELED
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
        self._cleanup()
        self.task_updated.emit(self.task)

    def _preflight(self) -> None:
        if not self.ffmpeg.ffmpeg_path.exists():
            raise FileNotFoundError("Az ffmpeg.exe nem található. Helyezd az ffmpeg.exe és ffprobe.exe fájlokat a tools/ffmpeg mappába.")
        output_dir = self.task.output_path.parent
        if not is_writable_directory(output_dir):
            raise PermissionError("A kimeneti mappa nem írható.")
        estimated = max(self.task.input_info.size_bytes, self.task.options.target_size_value.__round__() * 1024 * 1024)
        if not has_free_space(output_dir, int(estimated * 1.05)):
            raise OSError("Nincs elegendő szabad tárhely a kimeneti mappában.")

    def _run_pass(self, pass_number: int | None) -> None:
        self._current_pass = pass_number
        if pass_number == 1:
            self.task.status = TaskStatus.PASS1
        elif pass_number == 2:
            self.task.status = TaskStatus.PASS2
        else:
            self.task.status = TaskStatus.CONVERTING
        passlog = Path(self._passlog_dir.name) / "convertflow" if self._passlog_dir else None
        command = self.ffmpeg.build_command(self.task, pass_number, passlog, self.nvenc_available)
        if pass_number == 1:
            insert_at = max(0, len(command) - 1)
            command[insert_at:insert_at] = ["-f", "null"]
        self.process = QProcess(self)
        self.process.setProgram(command[0])
        self.process.setArguments(command[1:])
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_progress)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._process_error)
        self.process.started.connect(self._apply_process_priority)
        self.task_updated.emit(self.task)
        self.process.start()

    def _read_progress(self) -> None:
        if not self.process:
            return
        output = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        for line in output.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key == "out_time_ms":
                self._update_time(value)
            elif key == "speed":
                self.task.speed = value
            elif key == "progress":
                self.task.ffmpeg_status = value
        self.task.elapsed_seconds = time.monotonic() - self.started_at
        self.task_updated.emit(self.task)

    def _update_time(self, value: str) -> None:
        try:
            seconds = int(value) / 1_000_000
        except ValueError:
            return
        duration = max(self.task.input_info.duration_seconds, 0.1)
        base_progress = min(100.0, max(0.0, seconds / duration * 100))
        if self._current_pass == 1:
            self.task.progress = base_progress * 0.5
        elif self._current_pass == 2:
            self.task.progress = 50 + base_progress * 0.5
        else:
            self.task.progress = base_progress
        elapsed = max(time.monotonic() - self.started_at, 0.1)
        if self.task.progress > 0:
            eta = elapsed * (100 - self.task.progress) / self.task.progress
            self._eta = eta if self._eta is None else (self._eta * 0.75 + eta * 0.25)
            self.task.eta_seconds = self._eta

    def _finished(self, exit_code: int, _status: QProcess.ExitStatus) -> None:
        if self.task.status == TaskStatus.CANCELED:
            self.task_finished.emit(self.task)
            return
        if exit_code != 0:
            detail = ""
            if self.process:
                detail = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
            self._fail("Az FFmpeg hibával leállt.", detail)
            return
        if self._current_pass == 1:
            self._run_pass(2)
            return
        if self.task.options.preserve_source_date:
            shutil.copystat(self.task.input_info.path, self.task.output_path, follow_symlinks=True)
        self.task.status = TaskStatus.DONE
        self.task.progress = 100
        self._cleanup()
        self.task_updated.emit(self.task)
        self.task_finished.emit(self.task)

    def _process_error(self) -> None:
        if self.task.status != TaskStatus.CANCELED:
            self._fail("Az FFmpeg folyamat nem futtatható.", self.process.errorString() if self.process else "")

    def _apply_process_priority(self) -> None:
        if sys.platform != "win32" or not self.process:
            return
        priority = performance_profile(self.task.options.performance_mode).windows_priority
        if priority != "idle":
            return
        try:
            import ctypes

            idle_priority_class = 0x00000040
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            handle = kernel32.OpenProcess(0x0200 | 0x0400, False, int(self.process.processId()))
            if handle:
                try:
                    kernel32.SetPriorityClass(handle, idle_priority_class)
                    LOG.info("FFmpeg process priority set to idle for task %s", self.task.id)
                finally:
                    kernel32.CloseHandle(handle)
        except Exception:
            LOG.exception("Could not lower FFmpeg process priority")

    def _fail(self, message: str, technical: str) -> None:
        self.task.status = TaskStatus.FAILED
        self.task.error = message
        self.task.technical_error = technical
        self._cleanup()
        self.task_updated.emit(self.task)
        self.task_finished.emit(self.task)

    def _cleanup(self) -> None:
        if self._passlog_dir:
            self._passlog_dir.cleanup()
            self._passlog_dir = None
