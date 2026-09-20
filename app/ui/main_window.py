from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QFrame,
    QGraphicsOpacityEffect,
)

from app.core.conversion_queue import ConversionQueue
from app.core.ffmpeg_manager import FFmpegManager
from app.core.ffprobe_manager import FFprobeManager
from app.core.hardware_detection import detect_hardware
from app.core.models import ConversionTask, TaskStatus
from app.core.settings_manager import SettingsManager
from app.ui.conversion_item_widget import ConversionItemWidget
from app.ui.home_page import HomePage
from app.ui.settings_page import SettingsPage
from app.ui.video_compressor_page import VideoCompressorPage
from app.ui.video_converter_page import VideoConverterPage
from app.utils.file_utils import is_supported_video

LOG = logging.getLogger(__name__)

NAV_ITEMS = [
    ("Kezdőlap", "home", 0),
    ("Videó konvertálása", "convert", 1),
    ("Videó tömörítése", "compress", 2),
    ("Beállítások", "settings", 3),
]

FUTURE_ITEMS = [
    "Hang konvertálása",
    "Kép konvertálása",
    "Dokumentumok",
    "PDF-eszközök",
]


class NavButton(QPushButton):
    """Custom navigation button with icon and active state animation."""
    
    def __init__(self, text: str, icon_name: str, index: int, parent=None):
        super().__init__(text, parent)
        self.nav_index = index
        self.icon_name = icon_name
        self.setObjectName("navButton")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_icon()
        
    def _setup_icon(self) -> None:
        icon_map = {
            "home": "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
            "convert": "M7 16a4 4 0 0 1-4-4V5a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v7a4 4 0 0 1-4 4H7z",
            "compress": "M16 14v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z",
            "settings": "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z",
        }
        svg_data = f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="{icon_map.get(self.icon_name, "")}"/></svg>'
        
        self.setIcon(QIcon())
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.GlobalColor.transparent)
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtGui import QPainter
        renderer = QSvgRenderer(svg_data.encode())
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(20, 20))
    
    def enterEvent(self, event):
        if not self.isChecked():
            self.setProperty("hovered", True)
            self.style().unpolish(self)
            self.style().polish(self)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.setProperty("hovered", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, settings_manager: SettingsManager) -> None:
        super().__init__()
        self.settings_manager = settings_manager
        self.settings = settings_manager.get()
        self.ffmpeg = FFmpegManager(self.settings.custom_ffmpeg_dir)
        self.ffprobe = FFprobeManager(self.ffmpeg)
        self.hardware = detect_hardware(self.ffmpeg)
        self.queue = ConversionQueue(self.ffmpeg, self.settings.parallel_jobs)
        self.task_widgets: dict[str, ConversionItemWidget] = {}
        self.completed_actions: set[str] = set()
        self._current_page_index = 0
        self._page_animation: Optional[QPropertyAnimation] = None
        
        self.setWindowTitle("ConvertFlow Desktop")
        self.setMinimumSize(1280, 800)
        self.resize(1400, 880)
        self.setAcceptDrops(True)
        
        # Set window icon
        icon_path = Path(__file__).resolve().parent.parent.parent / "resources" / "icons" / "app.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self._build()
        self._connect()
        
        # Initial page setup
        self._switch_page(0, animate=False)
    
    def _build(self) -> None:
        # Root widget with horizontal layout
        root = QWidget()
        root.setObjectName("rootWidget")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ===== SIDEBAR =====
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Brand/Logo area
        brand_container = QWidget()
        brand_container.setObjectName("brandContainer")
        brand_layout = QVBoxLayout(brand_container)
        brand_layout.setContentsMargins(20, 24, 20, 20)
        brand_layout.setSpacing(8)
        
        # Logo + Text
        brand_row = QHBoxLayout()
        brand_row.setSpacing(12)
        
        logo_label = QLabel()
        logo_label.setFixedSize(36, 36)
        logo_pixmap = QPixmap(str(Path(__file__).resolve().parent.parent.parent / "resources" / "icons" / "logo.png"))
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setScaledContents(True)
        
        brand_text = QLabel("ConvertFlow")
        brand_text.setObjectName("brand")
        brand_text.setFont(brand_text.font())
        
        brand_row.addWidget(logo_label)
        brand_row.addWidget(brand_text)
        brand_row.addStretch()
        brand_layout.addLayout(brand_row)
        
        # Subtitle
        subtitle = QLabel("Video Converter & Compressor")
        subtitle.setObjectName("mutedText")
        subtitle.setFont(subtitle.font())
        brand_layout.addWidget(subtitle)
        
        sidebar_layout.addWidget(brand_container)
        
        # Navigation buttons
        self.nav_buttons: list[NavButton] = []
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(4)
        
        for text, icon_name, index in NAV_ITEMS:
            btn = NavButton(text, icon_name, index)
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        sidebar_layout.addWidget(nav_widget)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: #1e2a3d; border: none; max-height: 1px;")
        separator.setFixedHeight(1)
        sidebar_layout.addWidget(separator)
        
        # Future features section
        future_label = QLabel("KÖZELGŐ FUNKCIÓK")
        future_label.setObjectName("sectionTitle")
        future_label.setContentsMargins(16, 8, 16, 4)
        sidebar_layout.addWidget(future_label)
        
        future_widget = QWidget()
        future_layout = QVBoxLayout(future_widget)
        future_layout.setContentsMargins(8, 0, 8, 8)
        future_layout.setSpacing(4)
        
        for label in FUTURE_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(self._future_feature)
            future_layout.addWidget(btn)
        
        sidebar_layout.addWidget(future_widget)
        sidebar_layout.addStretch()
        
        # Version info at bottom
        version_label = QLabel("v1.0.0")
        version_label.setObjectName("mutedText")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setContentsMargins(0, 0, 0, 16)
        sidebar_layout.addWidget(version_label)
        
        layout.addWidget(sidebar)
        
        # ===== MAIN CONTENT AREA =====
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentStack")
        
        # Create pages
        self.home = HomePage(self.ffmpeg, self.settings, self.hardware)
        self.converter = VideoConverterPage()
        self.compressor = VideoCompressorPage()
        self.settings_page = SettingsPage(self.settings_manager, self.hardware.any_nvenc)
        
        for page in [self.home, self.converter, self.compressor, self.settings_page]:
            self.stack.addWidget(page)
        
        # Add fade effect for page transitions
        self._page_opacity_effect = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(self._page_opacity_effect)
        self._page_opacity_effect.setOpacity(1.0)
        
        layout.addWidget(self.stack, 1)
        
        self.setCentralWidget(root)
    
    def _connect(self) -> None:
        # Navigation buttons
        for btn in self.nav_buttons:
            btn.clicked.connect(self._on_nav_clicked)
        
        # Page signals
        self.converter.files_selected.connect(self.add_files)
        self.compressor.files_selected.connect(self.add_files)
        self.converter.start_all_requested.connect(lambda: self.queue.start())
        self.compressor.start_all_requested.connect(lambda: self.queue.start())
        self.queue.task_added.connect(self._task_added)
        self.queue.task_updated.connect(self._task_updated)
        self.queue.counts_changed.connect(self.home.set_counts)
        self.settings_page.settings_saved.connect(self._settings_saved)
        
        # Set initial active button
        self.nav_buttons[0].setChecked(True)
    
    def _on_nav_clicked(self) -> None:
        sender = self.sender()
        if isinstance(sender, NavButton):
            self._switch_page(sender.nav_index)
    
    def _switch_page(self, index: int, animate: bool = True) -> None:
        if index == self._current_page_index:
            return
        
        # Update button states
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        
        if animate:
            # Fade out
            self._page_animation = QPropertyAnimation(self._page_opacity_effect, b"opacity")
            self._page_animation.setDuration(120)
            self._page_animation.setStartValue(1.0)
            self._page_animation.setEndValue(0.0)
            self._page_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._page_animation.finished.connect(lambda: self._finish_page_switch(index))
            self._page_animation.start()
        else:
            self.stack.setCurrentIndex(index)
            self._current_page_index = index
    
    def _finish_page_switch(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self._current_page_index = index
        
        # Fade in
        self._page_animation = QPropertyAnimation(self._page_opacity_effect, b"opacity")
        self._page_animation.setDuration(150)
        self._page_animation.setStartValue(0.0)
        self._page_animation.setEndValue(1.0)
        self._page_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._page_animation.start()
    
    def add_files(self, paths: list[Path], page: VideoConverterPage | VideoCompressorPage | None = None) -> None:
        page = page or (self.compressor if self.stack.currentWidget() is self.compressor else self.converter)
        for path in paths:
            try:
                info = self.ffprobe.probe(path)
                page.show_video_info(info)
                task = page.make_task(info, Path(self.settings.default_output_dir))
                task.options.performance_mode = self.settings.performance_mode
                self.queue.add_task(task)
            except Exception as exc:
                LOG.exception("File add failed")
                self._show_error("Nem olvasható videó", f"{path.name}\n\n{exc}")
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # Visual feedback
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)
    
    def dragLeaveEvent(self, event) -> None:
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)
    
    def dropEvent(self, event: QDropEvent) -> None:
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        videos = [path for path in paths if is_supported_video(path)]
        if videos:
            self.add_files(videos)
        else:
            self._show_info("Nincs videó", "A behúzott fájlok között nincs támogatott videóformátum.")
    
    def closeEvent(self, event) -> None:
        if self.queue.has_active_jobs():
            reply = QMessageBox.question(
                self,
                "Konvertálás folyamatban",
                "Jelenleg konvertálás van folyamatban. Biztosan kilépsz?",
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.queue.cancel_all()
        event.accept()
    
    def _task_added(self, task: ConversionTask) -> None:
        widget = ConversionItemWidget(task)
        widget.start_requested.connect(self.queue.start)
        widget.cpu_retry_requested.connect(self._cpu_retry)
        widget.cancel_requested.connect(self.queue.cancel)
        widget.remove_requested.connect(self._remove_task)
        self.task_widgets[task.id] = widget
        target_page = self.compressor if task.options.mode.value == "compress" else self.converter
        target_page.add_item_widget(widget)
        
        # Auto-switch to the appropriate page if on home
        if self._current_page_index == 0:
            self._switch_page(1 if task.options.mode.value == "convert" else 2)
    
    def _task_updated(self, task: ConversionTask) -> None:
        widget = self.task_widgets.get(task.id)
        if widget:
            widget.update_task(task)
        if task.status == TaskStatus.DONE and task.id not in self.completed_actions:
            self.completed_actions.add(task.id)
            if self.settings.open_folder_after_conversion and task.output_path.parent.exists():
                os.startfile(str(task.output_path.parent))
            if self.settings.auto_remove_successful:
                self._remove_task(task.id)
    
    def _remove_task(self, task_id: str) -> None:
        self.queue.remove(task_id)
        widget = self.task_widgets.pop(task_id, None)
        if widget:
            widget.setParent(None)
            widget.deleteLater()
    
    def _cpu_retry(self, task_id: str) -> None:
        task = self.queue.tasks.get(task_id)
        if task:
            task.options.use_nvenc = False
            task.status = TaskStatus.WAITING
            task.error = ""
            task.technical_error = ""
            self.queue.start(task_id)
    
    def _settings_saved(self, settings) -> None:
        self.settings = settings
        self.queue.max_parallel = settings.parallel_jobs
        self._show_info("Mentve", "A beállítások mentése sikerült. Az FFmpeg útvonal módosítása újraindítás után biztosan érvényesül.")
    
    def _future_feature(self) -> None:
        self._show_info("Későbbi verzió", "Ez a funkció egy későbbi verzióban érkezik.")
    
    def _show_error(self, title: str, message: str) -> None:
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def _show_info(self, title: str, message: str) -> None:
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()