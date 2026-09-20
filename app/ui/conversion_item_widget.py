from __future__ import annotations

import os

from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QSizePolicy, QWidget
)

from app.core.models import ConversionTask, TaskStatus
from app.ui.dialogs import DetailsDialog
from app.utils.format_utils import format_duration


class ConversionItemWidget(QFrame):
    start_requested = Signal(str)
    cpu_retry_requested = Signal(str)
    cancel_requested = Signal(str)
    remove_requested = Signal(str)
    
    # Status colors
    STATUS_COLORS = {
        TaskStatus.WAITING: "#6b7a8e",
        TaskStatus.PREPARING: "#5b7cfa",
        TaskStatus.PASS1: "#5b7cfa",
        TaskStatus.PASS2: "#5b7cfa",
        TaskStatus.CONVERTING: "#00d4ff",
        TaskStatus.DONE: "#00e676",
        TaskStatus.CANCELED: "#ffd600",
        TaskStatus.FAILED: "#ff3d5c",
        TaskStatus.PAUSED: "#7c4dff",
    }
    
    def __init__(self, task: ConversionTask) -> None:
        super().__init__()
        self.task = task
        self.setObjectName("taskCard")
        self.setStyleSheet("""
            #taskCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #111820, stop:1 #0d121a);
                border: 1px solid #1e2a3d;
                border-radius: 12px;
            }
            #taskCard[status="running"] {
                border-color: #5b7cfa;
            }
            #taskCard[status="done"] {
                border-color: #00e676;
            }
            #taskCard[status="failed"] {
                border-color: #ff3d5c;
            }
        """)
        
        # File name
        self.name = QLabel()
        self.name.setObjectName("taskName")
        self.name.setWordWrap(False)
        self.name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.name.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 600;
                color: #f0f4fa;
                background: transparent;
            }
        """)
        
        # Status label with icon
        self.status = QLabel()
        self.status.setObjectName("taskStatus")
        self.status.setWordWrap(False)
        self.status.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.status.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #9ca8b8;
                background: transparent;
                font-family: "JetBrains Mono", monospace;
            }
        """)
        
        # Details
        self.details = QLabel()
        self.details.setObjectName("taskDetails")
        self.details.setWordWrap(False)
        self.details.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.details.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #6b7a8e;
                background: transparent;
                font-family: "JetBrains Mono", monospace;
            }
        """)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #0c1018;
                border: 1px solid #233044;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5b7cfa, stop:0.5 #00d4ff, stop:1 #5b7cfa);
                border-radius: 3px;
                margin: 1px;
            }
        """)
        
        # Buttons
        self.start_btn = QPushButton("Indít")
        self.cancel_btn = QPushButton("Stop")
        self.retry_btn = QPushButton("Újra")
        self.cpu_retry_btn = QPushButton("CPU retry")
        self.remove_btn = QPushButton("Törlés")
        self.folder_btn = QPushButton("Mappa")
        self.error_btn = QPushButton("Hiba")
        
        for button in [self.start_btn, self.cancel_btn, self.retry_btn, 
                       self.cpu_retry_btn, self.remove_btn, self.folder_btn, self.error_btn]:
            button.setFixedHeight(32)
            button.setMinimumWidth(80)
            button.setMaximumWidth(100)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet("""
                QPushButton {
                    font-size: 11px;
                    font-weight: 500;
                    padding: 4px 12px;
                }
            """)
        
        self.start_btn.setProperty("primary", True)
        self.start_btn.setToolTip("Feladat indítása")
        self.cancel_btn.setProperty("ghost", True)
        self.cancel_btn.setToolTip("Futó FFmpeg folyamat megszakítása")
        self.retry_btn.setProperty("ghost", True)
        self.retry_btn.setToolTip("Feladat újrapróbálása")
        self.cpu_retry_btn.setProperty("ghost", True)
        self.cpu_retry_btn.setToolTip("Újrapróbálás NVIDIA gyorsítás nélkül")
        self.remove_btn.setProperty("ghost", True)
        self.remove_btn.setProperty("danger", True)
        self.remove_btn.setToolTip("Feladat eltávolítása a listából")
        self.folder_btn.setProperty("ghost", True)
        self.folder_btn.setToolTip("Kimeneti mappa megnyitása")
        self.error_btn.setProperty("ghost", True)
        self.error_btn.setToolTip("Technikai hibarészletek megjelenítése")
        
        # Layout
        layout = QGridLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)
        
        # Row 0: Name (spans full width)
        layout.addWidget(self.name, 0, 0, 1, 7)
        
        # Row 1: Status + Progress
        layout.addWidget(self.status, 1, 0, 1, 4)
        layout.addWidget(self.progress, 1, 4, 1, 3)
        
        # Row 2: Details
        layout.addWidget(self.details, 2, 0, 1, 7)
        
        # Row 3: Buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.setContentsMargins(0, 4, 0, 0)
        
        for btn in [self.start_btn, self.cancel_btn, self.retry_btn, 
                    self.cpu_retry_btn, self.folder_btn, self.error_btn, self.remove_btn]:
            button_row.addWidget(btn)
        button_row.addStretch()
        
        layout.addLayout(button_row, 3, 0, 1, 7)
        
        # Connections
        self.start_btn.clicked.connect(lambda: self.start_requested.emit(self.task.id))
        self.retry_btn.clicked.connect(lambda: self.start_requested.emit(self.task.id))
        self.cpu_retry_btn.clicked.connect(lambda: self.cpu_retry_requested.emit(self.task.id))
        self.cancel_btn.clicked.connect(lambda: self.cancel_requested.emit(self.task.id))
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.task.id))
        self.folder_btn.clicked.connect(self._open_folder)
        self.error_btn.clicked.connect(self._show_error)
        
        self.update_task(task)
    
    def update_task(self, task: ConversionTask) -> None:
        self.task = task
        
        # Name
        self.name.setText(f"{task.input_info.path.name}  →  {task.output_path.name}")
        self.name.setToolTip(f"{task.input_info.path}\n→\n{task.output_path}")
        
        # Status text
        eta = format_duration(task.eta_seconds) if task.eta_seconds is not None else "--:--"
        elapsed = format_duration(task.elapsed_seconds)
        speed = task.speed or "—"
        
        status_text = f"{task.status.value}  •  {task.progress:.1f}%  •  {elapsed}  •  ETA: {eta}  •  {speed}"
        self.status.setText(status_text)
        
        # Update status color
        color = self.STATUS_COLORS.get(task.status, "#9ca8b8")
        self.status.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {color};
                background: transparent;
                font-family: "JetBrains Mono", monospace;
                font-weight: 500;
            }}
        """)
        
        # Details
        self.details.setText(f"Kimenet: {task.output_path.name}  |  Mappa: {task.output_path.parent.name}  |  FFmpeg: {task.ffmpeg_status or '—'}")
        self.details.setToolTip(str(task.output_path))
        
        # Progress bar
        self.progress.setValue(int(task.progress))
        
        # Update card status property for styling
        if task.status in {TaskStatus.PREPARING, TaskStatus.PASS1, TaskStatus.PASS2, TaskStatus.CONVERTING}:
            self.setProperty("status", "running")
        elif task.status == TaskStatus.DONE:
            self.setProperty("status", "done")
        elif task.status == TaskStatus.FAILED:
            self.setProperty("status", "failed")
        else:
            self.setProperty("status", "")
        
        # Force style update
        self.style().unpolish(self)
        self.style().polish(self)
        
        # Button states
        is_running = task.status in {TaskStatus.PREPARING, TaskStatus.PASS1, TaskStatus.PASS2, TaskStatus.CONVERTING}
        is_done = task.status == TaskStatus.DONE
        is_failed = task.status == TaskStatus.FAILED
        is_waiting = task.status == TaskStatus.WAITING
        is_canceled = task.status == TaskStatus.CANCELED
        
        self.start_btn.setEnabled(is_waiting)
        self.start_btn.setVisible(is_waiting or is_canceled or is_failed)
        
        self.cancel_btn.setEnabled(is_running)
        self.cancel_btn.setVisible(is_running)
        
        self.retry_btn.setVisible(is_failed or is_canceled)
        self.cpu_retry_btn.setVisible(is_failed and task.options.use_nvenc)
        self.folder_btn.setEnabled(task.output_path.parent.exists())
        self.folder_btn.setVisible(is_done or task.output_path.exists())
        self.error_btn.setVisible(bool(task.error or task.technical_error))
    
    def _open_folder(self) -> None:
        if self.task.output_path.parent.exists():
            os.startfile(str(self.task.output_path.parent))
    
    def _show_error(self) -> None:
        DetailsDialog("Hiba részletei", f"{self.task.error}\n\n{self.task.technical_error}", self).exec()