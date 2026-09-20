from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget,
    QScrollArea, QGroupBox
)

from app.core.performance_profiles import PERFORMANCE_MODES
from app.core.settings_manager import AppSettings, SettingsManager


class SettingsSection(QGroupBox):
    """Styled settings section group box."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setObjectName("settingsSection")
        self.setStyleSheet("""
            #settingsSection {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #111820, stop:1 #0d121a);
                border: 1px solid #1e2a3d;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: 600;
                color: #9ca8b8;
                font-size: 12px;
            }
            #settingsSection::title {
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


class SettingsPage(QWidget):
    settings_saved = Signal(object)
    settings_reset = Signal()
    
    def __init__(self, manager: SettingsManager, nvenc_supported: bool) -> None:
        super().__init__()
        self.manager = manager
        self.nvenc_supported = nvenc_supported
        self._build()
        self.load(manager.get())
    
    def _build(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)
        
        title = QLabel("Beállítások")
        title.setObjectName("pageTitle")
        title.setStyleSheet("""
            QLabel {
                font-size: 26px;
                font-weight: 700;
                color: #f0f4fa;
                letter-spacing: -0.5px;
            }
        """)
        
        subtitle = QLabel("Alapértelmezések és alkalmazás beállításai")
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
        
        main_layout.addWidget(header)
        
        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        
        # ===== GENERAL SETTINGS =====
        general_section = SettingsSection("Általános")
        general_layout = QFormLayout(general_section)
        general_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        general_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        general_layout.setSpacing(12)
        general_layout.setContentsMargins(16, 24, 16, 16)
        
        # Output directory
        output_row = QWidget()
        output_layout = QHBoxLayout(output_row)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(8)
        
        self.output_dir = QLabel()
        self.output_dir.setStyleSheet("""
            QLabel {
                background: #0d121a;
                border: 1px solid #233044;
                border-radius: 8px;
                padding: 8px 12px;
                color: #f0f4fa;
                font-family: "JetBrains Mono", monospace;
                font-size: 12px;
            }
        """)
        self.output_dir.setWordWrap(True)
        self.output_dir.setMinimumHeight(40)
        
        pick_dir = QPushButton("Tallózás")
        pick_dir.setProperty("ghost", True)
        pick_dir.setFixedHeight(40)
        pick_dir.setCursor(Qt.CursorShape.PointingHandCursor)
        pick_dir.clicked.connect(self._pick_dir)
        
        output_layout.addWidget(self.output_dir, 1)
        output_layout.addWidget(pick_dir)
        
        general_layout.addRow("Alapértelmezett kimeneti mappa", output_row)
        
        # NVENC
        self.use_nvenc = QCheckBox("NVIDIA hardveres gyorsítás használata (NVENC)")
        self.use_nvenc.setEnabled(self.nvenc_supported)
        self.use_nvenc.setToolTip("Használja az NVIDIA GPU-t a videókódoláshoz, ha elérhető")
        if not self.nvenc_supported:
            self.use_nvenc.setToolTip("Az FFmpeg nem jelez elérhető NVENC kódolót")
            self.use_nvenc.setStyleSheet("color: #6b7a8e;")
        general_layout.addRow("", self.use_nvenc)
        
        content_layout.addWidget(general_section)
        
        # ===== DEFAULT ENCODING SETTINGS =====
        encoding_section = SettingsSection("Alapértelmezett kódolás")
        encoding_layout = QFormLayout(encoding_section)
        encoding_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        encoding_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        encoding_layout.setSpacing(12)
        encoding_layout.setContentsMargins(16, 24, 16, 16)
        
        self.codec = QComboBox()
        self.codec.addItems(["H.264", "H.265 / HEVC", "AV1", "VP9"])
        self.codec.setToolTip("Alapértelmezett videókodek az új feladatokhoz")
        
        self.profile = QComboBox()
        self.profile.addItems(["Eredeti minőség", "Kiváló minőség", "Jó minőség", "Kiegyensúlyozott", "Kis fájlméret"])
        self.profile.setToolTip("Alapértelmezett minőségi profil")
        
        self.audio_bitrate = QComboBox()
        self.audio_bitrate.addItems(["96", "128", "160", "192", "256", "320"])
        self.audio_bitrate.setToolTip("Alapértelmezett hang bitráta (kbps)")
        
        encoding_layout.addRow("Videókodek", self.codec)
        encoding_layout.addRow("Minőségi profil", self.profile)
        encoding_layout.addRow("Hang bitráta (kbps)", self.audio_bitrate)
        
        content_layout.addWidget(encoding_section)
        
        # ===== BEHAVIOR SETTINGS =====
        behavior_section = SettingsSection("Viselkedés")
        behavior_layout = QFormLayout(behavior_section)
        behavior_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        behavior_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        behavior_layout.setSpacing(12)
        behavior_layout.setContentsMargins(16, 24, 16, 16)
        
        self.open_folder = QCheckBox("Konvertálás után a kimeneti mappa megnyitása")
        self.open_folder.setToolTip("Automatikusan megnyitja a kimeneti mappát a fájlkezelőben")
        behavior_layout.addRow("", self.open_folder)
        
        self.auto_remove = QCheckBox("Sikeres feladatok automatikus eltávolítása a listából")
        self.auto_remove.setToolTip("A befejezett feladatokat automatikusan eltávolítja a várólista-ból")
        behavior_layout.addRow("", self.auto_remove)
        
        self.preserve_date = QCheckBox("Forrásfájl dátumának megőrzése")
        self.preserve_date.setToolTip("A kimeneti fájl módosítási ideje megegyezik a forrás fájéval")
        behavior_layout.addRow("", self.preserve_date)
        
        content_layout.addWidget(behavior_section)
        
        # ===== PERFORMANCE SETTINGS =====
        perf_section = SettingsSection("Teljesítmény")
        perf_layout = QFormLayout(perf_section)
        perf_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        perf_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        perf_layout.setSpacing(12)
        perf_layout.setContentsMargins(16, 24, 16, 16)
        
        self.parallel = QSpinBox()
        self.parallel.setRange(1, 2)
        self.parallel.setToolTip("Egyidejű konvertálások száma (max 2 a stabilitás érdekében)")
        
        self.performance_mode = QComboBox()
        self.performance_mode.addItems(PERFORMANCE_MODES)
        self.performance_mode.setToolTip(
            "Halk: max 2 szál, alacsony prioritás, lassabb de csendes\n"
            "Normál: kiegyensúlyozott\n"
            "Gyors: gyorsabb feldolgozás, magasabb CPU használat"
        )
        
        perf_layout.addRow("Párhuzamos konvertálások", self.parallel)
        perf_layout.addRow("Teljesítmény mód", self.performance_mode)
        
        content_layout.addWidget(perf_section)
        
        # ===== FFMPEG SETTINGS =====
        ffmpeg_section = SettingsSection("FFmpeg")
        ffmpeg_layout = QFormLayout(ffmpeg_section)
        ffmpeg_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        ffmpeg_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        ffmpeg_layout.setSpacing(12)
        ffmpeg_layout.setContentsMargins(16, 24, 16, 16)
        
        ffmpeg_row = QWidget()
        ffmpeg_row_layout = QHBoxLayout(ffmpeg_row)
        ffmpeg_row_layout.setContentsMargins(0, 0, 0, 0)
        ffmpeg_row_layout.setSpacing(8)
        
        self.ffmpeg_dir = QLabel()
        self.ffmpeg_dir.setStyleSheet("""
            QLabel {
                background: #0d121a;
                border: 1px solid #233044;
                border-radius: 8px;
                padding: 8px 12px;
                color: #f0f4fa;
                font-family: "JetBrains Mono", monospace;
                font-size: 12px;
            }
        """)
        self.ffmpeg_dir.setWordWrap(True)
        self.ffmpeg_dir.setMinimumHeight(40)
        
        pick_ffmpeg = QPushButton("Tallózás")
        pick_ffmpeg.setProperty("ghost", True)
        pick_ffmpeg.setFixedHeight(40)
        pick_ffmpeg.setCursor(Qt.CursorShape.PointingHandCursor)
        pick_ffmpeg.clicked.connect(self._pick_ffmpeg)
        
        ffmpeg_row_layout.addWidget(self.ffmpeg_dir, 1)
        ffmpeg_row_layout.addWidget(pick_ffmpeg)
        
        ffmpeg_layout.addRow("Egyedi FFmpeg mappa", ffmpeg_row)
        
        # FFmpeg version info
        self.ffmpeg_version = QLabel()
        self.ffmpeg_version.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #6b7a8e;
                font-size: 12px;
                font-family: "JetBrains Mono", monospace;
            }
        """)
        ffmpeg_layout.addRow("Verzió", self.ffmpeg_version)
        
        content_layout.addWidget(ffmpeg_section)
        
        # ===== LOGGING =====
        log_section = SettingsSection("Naplózás")
        log_layout = QFormLayout(log_section)
        log_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        log_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        log_layout.setSpacing(12)
        log_layout.setContentsMargins(16, 24, 16, 16)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setToolTip("Naplózási részletesség")
        
        log_layout.addRow("Naplózási szint", self.log_level)
        
        content_layout.addWidget(log_section)
        
        # NVENC hint
        if not self.nvenc_supported:
            hint = QLabel("Az NVIDIA gyorsítás letiltva, mert az FFmpeg nem jelez NVENC támogatást.")
            hint.setObjectName("mutedText")
            hint.setStyleSheet("""
                QLabel {
                    background: #1a150d;
                    border: 1px solid #4a3a1a;
                    border-radius: 8px;
                    padding: 12px;
                    color: #d4b870;
                    font-size: 13px;
                }
            """)
            hint.setWordWrap(True)
            content_layout.addWidget(hint)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll, 1)
        
        # ===== ACTION BUTTONS =====
        button_bar = QWidget()
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        self.reset_btn = QPushButton("Beállítások visszaállítása")
        self.reset_btn.setProperty("ghost", True)
        self.reset_btn.setFixedHeight(40)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.clicked.connect(self.reset)
        
        self.save_btn = QPushButton("Beállítások mentése")
        self.save_btn.setProperty("primary", True)
        self.save_btn.setFixedHeight(40)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.save)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addWidget(button_bar)
    
    def load(self, settings: AppSettings) -> None:
        self.output_dir.setText(settings.default_output_dir)
        self.use_nvenc.setChecked(settings.use_nvenc and self.nvenc_supported)
        self.codec.setCurrentText(settings.default_video_codec)
        self.profile.setCurrentText(settings.default_quality_profile)
        self.audio_bitrate.setCurrentText(str(settings.default_audio_bitrate))
        self.open_folder.setChecked(settings.open_folder_after_conversion)
        self.auto_remove.setChecked(settings.auto_remove_successful)
        self.parallel.setValue(settings.parallel_jobs)
        self.performance_mode.setCurrentText(settings.performance_mode)
        self.log_level.setCurrentText(settings.log_level)
        self.preserve_date.setChecked(settings.preserve_source_date)
        
        ffmpeg_path = settings.custom_ffmpeg_dir or "tools/ffmpeg"
        self.ffmpeg_dir.setText(ffmpeg_path)
        
        # Try to get FFmpeg version
        try:
            from app.core.ffmpeg_manager import FFmpegManager
            ffmpeg = FFmpegManager(settings.custom_ffmpeg_dir)
            self.ffmpeg_version.setText(ffmpeg.version())
        except Exception:
            self.ffmpeg_version.setText("Ismeretlen")
    
    def save(self) -> None:
        settings = AppSettings(
            default_output_dir=self.output_dir.text(),
            use_nvenc=self.use_nvenc.isChecked(),
            default_video_codec=self.codec.currentText(),
            default_quality_profile=self.profile.currentText(),
            default_audio_bitrate=int(self.audio_bitrate.currentText()),
            open_folder_after_conversion=self.open_folder.isChecked(),
            auto_remove_successful=self.auto_remove.isChecked(),
            parallel_jobs=self.parallel.value(),
            performance_mode=self.performance_mode.currentText(),
            log_level=self.log_level.currentText(),
            custom_ffmpeg_dir="" if self.ffmpeg_dir.text() == "tools/ffmpeg" else self.ffmpeg_dir.text(),
            preserve_source_date=self.preserve_date.isChecked(),
        )
        self.manager.save(settings)
        self.settings_saved.emit(settings)
    
    def reset(self) -> None:
        self.load(self.manager.reset())
        self.settings_reset.emit()
    
    def _pick_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Kimeneti mappa", self.output_dir.text())
        if path:
            self.output_dir.setText(path)
    
    def _pick_ffmpeg(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "FFmpeg mappa", str(Path.cwd()))
        if path:
            self.ffmpeg_dir.setText(path)