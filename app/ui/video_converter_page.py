from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QGroupBox,
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.core.models import ConversionMode, ConversionOptions, ConversionTask, VideoInfo
from app.core.video_profiles import CONTAINER_CODECS
from app.utils.file_utils import default_output_name, ensure_unique_path, is_supported_video
from app.utils.format_utils import format_duration, format_file_size


class _DropZone(QFrame):
    """Drop zone widget that handles drag and drop for files."""
    
    files_dropped = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            #dropZone {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f1620, stop:1 #0d121a);
                border: 2px dashed #233044;
                border-radius: 12px;
            }
            #dropZone[dragActive="true"] {
                border-color: #5b7cfa;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #151e2d, stop:1 #111820);
            }
        """)
        
        drop_layout = QHBoxLayout(self)
        drop_layout.setContentsMargins(20, 0, 20, 0)
        drop_layout.setSpacing(16)
        
        drop_icon = QLabel()
        drop_icon.setFixedSize(32, 32)
        drop_pixmap = self._create_svg_pixmap(
            '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>',
            "#5b7cfa"
        )
        drop_icon.setPixmap(drop_pixmap)
        
        drop_text = QLabel("Videófájlokat ide húzhatod, vagy kattints a \"Fájl hozzáadása\" gombra")
        drop_text.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6b7a8e;
                background: transparent;
            }
        """)
        
        drop_layout.addWidget(drop_icon)
        drop_layout.addWidget(drop_text, 1)
        drop_layout.addStretch()
    
    def _create_svg_pixmap(self, svg: str, color: str) -> QPixmap:
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtGui import QPainter
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        svg_colored = svg.replace('currentColor', color)
        renderer = QSvgRenderer(svg_colored.encode())
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
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
            self.files_dropped.emit(videos)
        else:
            QMessageBox.information(self, "Nincs videó", "A behúzott fájlok között nincs támogatott videóformátum.")


class SectionGroup(QGroupBox):
    """Styled group box for settings sections."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setObjectName("settingsGroup")
        self.setStyleSheet("""
            #settingsGroup {
                background: transparent;
                border: 1px solid #1e2a3d;
                border-radius: 10px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: 600;
                color: #9ca8b8;
                font-size: 12px;
            }
            #settingsGroup::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                top: 0px;
                padding: 0 8px;
                background: #0a0e14;
                color: #9ca8b8;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)


class VideoConverterPage(QWidget):
    files_selected = Signal(list, object)
    start_all_requested = Signal()
    
    def __init__(self, mode: ConversionMode = ConversionMode.CONVERT) -> None:
        super().__init__()
        self.mode = mode
        self.items: dict[str, QWidget] = {}
        self._dropped_files: list[Path] = []
        self.setAcceptDrops(True)
        self._build()
    
    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # ===== HEADER =====
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)
        
        title_text = "Videó konvertálása" if self.mode == ConversionMode.CONVERT else "Videó tömörítése"
        title = QLabel(title_text)
        title.setObjectName("pageTitle")
        title.setStyleSheet("""
            QLabel {
                font-size: 26px;
                font-weight: 700;
                color: #f0f4fa;
                letter-spacing: -0.5px;
            }
        """)
        
        subtitle = QLabel(
            "Húzd ide a videófájlokat, vagy kattints a hozzáadás gombra"
            if self.mode == ConversionMode.CONVERT
            else "Add meg a célméretet vagy minőséget, majd add hozzá a videókat"
        )
        subtitle.setObjectName("mutedText")
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #9ca8b8;
                font-weight: 400;
            }
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Action buttons
        self.add_btn = QPushButton("Fájl hozzáadása")
        self.add_btn.setProperty("primary", True)
        self.add_btn.setFixedHeight(40)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._choose_files)
        
        self.start_all_btn = QPushButton("Összes várakozó indítása")
        self.start_all_btn.setProperty("ghost", True)
        self.start_all_btn.setFixedHeight(40)
        self.start_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_all_btn.clicked.connect(self.start_all_requested.emit)
        
        header_layout.addWidget(self.add_btn)
        header_layout.addWidget(self.start_all_btn)
        
        layout.addWidget(header)
        
        # ===== DROP ZONE =====
        self.drop_zone = _DropZone()
        self.drop_zone.setFixedHeight(80)
        layout.addWidget(self.drop_zone)
        
        # ===== MAIN CONTENT SPLIT =====
        body = QHBoxLayout()
        body.setSpacing(16)
        layout.addLayout(body, 1)
        
        # ===== SETTINGS PANEL (LEFT) =====
        settings_panel = QFrame()
        settings_panel.setObjectName("settingsPanel")
        settings_panel.setMinimumWidth(380)
        settings_panel.setMaximumWidth(460)
        settings_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        settings_panel.setStyleSheet("""
            #settingsPanel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f1620, stop:1 #0d121a);
                border: 1px solid #1e2a3d;
                border-radius: 14px;
            }
        """)
        
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)
        
        settings_content = QWidget()
        self.settings_layout = QVBoxLayout(settings_content)
        self.settings_layout.setContentsMargins(16, 16, 16, 16)
        self.settings_layout.setSpacing(16)
        
        # --- Output Format Section ---
        format_group = SectionGroup("Kimeneti formátum")
        format_layout = QFormLayout(format_group)
        format_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        format_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        format_layout.setSpacing(12)
        format_layout.setContentsMargins(16, 24, 16, 16)
        
        self.container = QComboBox()
        self.container.addItems(["mp4", "mkv", "mov", "webm", "avi"])
        self.container.setToolTip("Kimeneti konténer formátum")
        self.container.currentTextChanged.connect(self._sync_codecs)
        
        format_layout.addRow("Konténer", self.container)
        self.settings_layout.addWidget(format_group)
        
        # --- Video Settings Section ---
        video_group = SectionGroup("Videó beállítások")
        video_layout = QFormLayout(video_group)
        video_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        video_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        video_layout.setSpacing(12)
        video_layout.setContentsMargins(16, 24, 16, 16)
        
        self.profile = QComboBox()
        self.profile.addItems(["Eredeti minőség", "Kiváló minőség", "Jó minőség", "Kiegyensúlyozott", "Kis fájlméret", "Egyéni beállítások"])
        self.profile.setToolTip("Minőségi profil a videókódoláshoz")
        
        self.resolution = QComboBox()
        self.resolution.addItems(["Eredeti", "3840 × 2160", "2560 × 1440", "1920 × 1080", "1280 × 720", "854 × 480"])
        self.resolution.setToolTip("Kimeneti felbontás (arány megmarad)")
        
        self.fps = QComboBox()
        self.fps.addItems(["Eredeti", "60", "50", "30", "25", "24"])
        self.fps.setToolTip("Kimeneti képkockasebesség")
        
        self.codec = QComboBox()
        self.codec.setToolTip("Videókodek a kiválasztott konténerhez")
        
        self.use_nvenc = QCheckBox("NVIDIA hardveres gyorsítás (NVENC)")
        self.use_nvenc.setToolTip("Használja az NVIDIA GPU-t a kódoláshoz, ha elérhető")
        
        video_layout.addRow("Minőségi profil", self.profile)
        video_layout.addRow("Felbontás", self.resolution)
        video_layout.addRow("FPS", self.fps)
        video_layout.addRow("Videókodek", self.codec)
        video_layout.addRow("", self.use_nvenc)
        
        self.settings_layout.addWidget(video_group)
        
        # --- Audio Settings Section ---
        audio_group = SectionGroup("Hang beállítások")
        audio_layout = QFormLayout(audio_group)
        audio_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        audio_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        audio_layout.setSpacing(12)
        audio_layout.setContentsMargins(16, 24, 16, 16)
        
        self.audio = QComboBox()
        self.audio.addItems(["AAC", "MP3", "Opus", "Eredeti hangsáv másolása", "Hang eltávolítása"])
        self.audio.setToolTip("Hangkodek vagy mód")
        
        self.audio_bitrate = QComboBox()
        self.audio_bitrate.addItems(["96", "128", "160", "192", "256", "320"])
        self.audio_bitrate.setToolTip("Hang bitráta kbps-ben")
        
        self.keep_audio = QCheckBox("Hangsávok megtartása")
        self.keep_audio.setChecked(True)
        self.keep_audio.setToolTip("Az összes hangsáv megtartása a kimenetben")
        
        audio_layout.addRow("Hang mód", self.audio)
        audio_layout.addRow("Hang bitráta (kbps)", self.audio_bitrate)
        audio_layout.addRow("", self.keep_audio)
        
        self.settings_layout.addWidget(audio_group)
        
        # --- Advanced Section ---
        advanced_group = SectionGroup("Speciális")
        advanced_layout = QFormLayout(advanced_group)
        advanced_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        advanced_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        advanced_layout.setSpacing(12)
        advanced_layout.setContentsMargins(16, 24, 16, 16)
        
        self.keep_meta = QCheckBox("Metaadatok megtartása")
        self.keep_meta.setChecked(True)
        self.keep_meta.setToolTip("Globális metaadatok átmásolása a kimeneti fájlba")
        
        self.keep_subs = QCheckBox("Feliratok megtartása")
        self.keep_subs.setChecked(True)
        self.keep_subs.setToolTip("Beágyazott feliratok átmásolása")
        
        self.preserve_date = QCheckBox("Forrásfájl dátumának megőrzése")
        self.preserve_date.setToolTip("A kimeneti fájl módosítási ideje megegyezik a forráséval")
        
        advanced_layout.addRow("", self.keep_meta)
        advanced_layout.addRow("", self.keep_subs)
        advanced_layout.addRow("", self.preserve_date)
        
        self.settings_layout.addWidget(advanced_group)
        self.settings_layout.addStretch()
        
        settings_scroll.setWidget(settings_content)
        
        settings_panel_layout = QVBoxLayout(settings_panel)
        settings_panel_layout.setContentsMargins(0, 0, 0, 0)
        settings_panel_layout.addWidget(settings_scroll)
        
        body.addWidget(settings_panel)
        
        # ===== TASKS PANEL (RIGHT) =====
        tasks_panel = QWidget()
        tasks_layout = QVBoxLayout(tasks_panel)
        tasks_layout.setContentsMargins(0, 0, 0, 0)
        tasks_layout.setSpacing(12)
        
        # Selected files info
        self.info_list = QListWidget()
        self.info_list.setObjectName("infoList")
        self.info_list.setMaximumHeight(100)
        self.info_list.setStyleSheet("""
            #infoList {
                background: #0d121a;
                border: 1px solid #1e2a3d;
                border-radius: 10px;
                padding: 8px;
                font-family: "JetBrains Mono", "Consolas", monospace;
                font-size: 12px;
            }
        """)
        tasks_layout.addWidget(self.info_list)
        
        # Task list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        
        self.scroll.setWidget(self.list_widget)
        tasks_layout.addWidget(self.scroll, 1)
        
        body.addWidget(tasks_panel, 1)
        
        # Initialize
        self._sync_codecs()
        
        # Connect drop zone signal
        self.drop_zone.files_dropped.connect(lambda paths: self.files_selected.emit(paths, self))
    
    def _create_svg_pixmap(self, svg: str, color: str) -> QPixmap:
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtGui import QPainter
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        # Replace currentColor with actual color
        svg_colored = svg.replace('currentColor', color)
        renderer = QSvgRenderer(svg_colored.encode())
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap
    
    def set_nvenc_enabled(self, supported: bool, default_checked: bool) -> None:
        self.use_nvenc.setEnabled(supported)
        self.use_nvenc.setChecked(supported and default_checked)
        self.use_nvenc.setToolTip("" if supported else "Az FFmpeg nem jelez elérhető NVENC kódolót.")
        if not supported:
            self.use_nvenc.setStyleSheet("""
                QCheckBox {
                    color: #6b7a8e;
                }
                QCheckBox::indicator {
                    border-color: #233044;
                }
            """)
    
    def options(self) -> ConversionOptions:
        return ConversionOptions(
            mode=self.mode,
            container=self.container.currentText(),
            video_codec=self.codec.currentText(),
            audio_mode=self.audio.currentText(),
            audio_bitrate_kbps=int(self.audio_bitrate.currentText()),
            quality_profile=self.profile.currentText(),
            resolution=self.resolution.currentText(),
            fps=self.fps.currentText(),
            keep_metadata=self.keep_meta.isChecked(),
            keep_subtitles=self.keep_subs.isChecked(),
            keep_audio_tracks=self.keep_audio.isChecked(),
            preserve_source_date=self.preserve_date.isChecked(),
            use_nvenc=self.use_nvenc.isChecked(),
        )
    
    def make_task(self, info: VideoInfo, output_dir: Path) -> ConversionTask:
        opts = self.options()
        out = ensure_unique_path(output_dir / default_output_name(info.path, "convertflow", opts.container))
        return ConversionTask(info, out, opts)
    
    def add_item_widget(self, widget: QWidget) -> None:
        self.list_layout.insertWidget(self.list_layout.count() - 1, widget)
    
    def show_video_info(self, info: VideoInfo) -> None:
        text = (
            f"{info.path.name}  |  "
            f"{format_file_size(info.size_bytes)}  |  "
            f"{format_duration(info.duration_seconds)}  |  "
            f"{info.width}×{info.height}  |  "
            f"{info.fps:.2f} FPS  |  "
            f"v: {info.video_codec}  |  "
            f"a: {info.audio_codec} ({info.audio_streams}ch)"
        )
        self.info_list.addItem(text)
    
    def _choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Videófájlok kiválasztása", "",
            "Videók (*.mp4 *.mkv *.mov *.avi *.webm *.wmv *.m4v *.mpeg *.mpg *.flv *.ts *.mts *.m2ts)"
        )
        selected = [Path(p) for p in paths if is_supported_video(Path(p))]
        if not selected and paths:
            QMessageBox.warning(self, "Nem támogatott fájl", "A kiválasztott fájlok között nincs támogatott videóformátum.")
        if selected:
            self.files_selected.emit(selected, self)
    
    def _sync_codecs(self) -> None:
        current = self.codec.currentText()
        self.codec.clear()
        self.codec.addItems(CONTAINER_CODECS[self.container.currentText()])
        if current:
            index = self.codec.findText(current)
            if index >= 0:
                self.codec.setCurrentIndex(index)