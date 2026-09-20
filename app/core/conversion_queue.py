from __future__ import annotations

from collections import deque

from PySide6.QtCore import QObject, Signal

from app.core.conversion_worker import ConversionWorker
from app.core.ffmpeg_manager import FFmpegManager
from app.core.models import ConversionTask, TaskStatus


class ConversionQueue(QObject):
    task_added = Signal(object)
    task_updated = Signal(object)
    counts_changed = Signal(int, int)

    def __init__(self, ffmpeg: FFmpegManager, max_parallel: int = 1) -> None:
        super().__init__()
        self.ffmpeg = ffmpeg
        self.max_parallel = max(1, min(2, max_parallel))
        self.nvenc_available = ffmpeg.available_nvenc_encoders()
        self.waiting: deque[ConversionTask] = deque()
        self.running: dict[str, ConversionWorker] = {}
        self.tasks: dict[str, ConversionTask] = {}

    def add_task(self, task: ConversionTask) -> None:
        self.tasks[task.id] = task
        self.waiting.append(task)
        self.task_added.emit(task)
        self._emit_counts()

    def start(self, task_id: str | None = None) -> None:
        if task_id:
            task = self.tasks.get(task_id)
            if task and task.status in {TaskStatus.FAILED, TaskStatus.CANCELED}:
                task.status = TaskStatus.WAITING
                task.progress = 0
                self.waiting.appendleft(task)
        self._pump()

    def cancel(self, task_id: str) -> None:
        worker = self.running.get(task_id)
        if worker:
            worker.cancel()
            return
        for task in list(self.waiting):
            if task.id == task_id:
                self.waiting.remove(task)
                task.status = TaskStatus.CANCELED
                self.task_updated.emit(task)
                self._emit_counts()
                return

    def remove(self, task_id: str) -> None:
        self.cancel(task_id)
        self.tasks.pop(task_id, None)
        self._emit_counts()

    def has_active_jobs(self) -> bool:
        return bool(self.running)

    def cancel_all(self) -> None:
        for task_id in list(self.running):
            self.cancel(task_id)
        self.waiting.clear()
        self._emit_counts()

    def _pump(self) -> None:
        while self.waiting and len(self.running) < self.max_parallel:
            task = self.waiting.popleft()
            if task.status not in {TaskStatus.WAITING, TaskStatus.FAILED, TaskStatus.CANCELED}:
                continue
            worker = ConversionWorker(self.ffmpeg, task, self.nvenc_available)
            worker.task_updated.connect(self.task_updated.emit)
            worker.task_finished.connect(self._finished)
            self.running[task.id] = worker
            worker.start()
        self._emit_counts()

    def _finished(self, task: ConversionTask) -> None:
        self.running.pop(task.id, None)
        self.task_updated.emit(task)
        self._pump()

    def _emit_counts(self) -> None:
        self.counts_changed.emit(len(self.running), len(self.waiting))
