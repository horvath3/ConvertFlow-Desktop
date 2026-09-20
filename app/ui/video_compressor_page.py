from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QFormLayout, QLabel, QSpinBox, QHBoxLayout, QWidget, QGroupBox, QVBoxLayout

from app.core.models import CompressionMode, ConversionMode, ConversionOptions, ConversionTask, VideoInfo
from app.core.target_size_calculator import calculate_video_bitrate, target_size_to_bytes
from app.ui.video_converter_page import VideoConverterPage
from app.utils.file_utils import default_output_name, ensure_unique_path
from app.utils.format_utils import format_file_size


class VideoCompressorPage(VideoConverterPage):
    def __init__(self) -> None:
        super().__init__(ConversionMode.COMPRESS)
        self._add_compressor_controls()
    
    def _add_compressor_controls(self) -> None:
        # Create a dedicated compressor section at the top of settings
        compressor_group = self._create_compressor_group()
        self.settings_layout.insertWidget(0, compressor_group)
        
        # Connect mode change to update UI
        self.compress_mode.currentTextChanged.connect(self._on_compress_mode_changed)
        self.target_value.valueChanged.connect(self._update_estimate)
        self.target_unit.currentTextChanged.connect(self._update_estimate)
        self.video_bitrate.valueChanged.connect(self._update_estimate)
        self.max_bitrate.valueChanged.connect(self._update_estimate)
    
    def _create_compressor_group(self) -> QWidget:
        from PySide6.QtWidgets import QGroupBox, QVBoxLayout
        
        group = QGroupBox("Tömörítési beállítások")
        group.setObjectName("compressorGroup")
        group.setStyleSheet("""
            #compressorGroup {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #111820, stop:1 #0d121a);
                border: 1px solid #5b7cfa44;
                border-radius: 10px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: 600;
                color: #5b7cfa;
                font-size: 12px;
            }
            #compressorGroup::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                top: 0px;
                padding: 0 8px;
                background: #0a0e14;
                color: #5b7cfa;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(12)
        
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setSpacing(10)
        
        self.compress_mode = QComboBox()
        self.compress_mode.addItems(["Minőség alapján", "Célfájlméret alapján", "Egyéni bitráta alapján"])
        self.compress_mode.setToolTip("Hogyan legyen meghatározva a tömörítés erőssége")
        
        self.compress_profile = QComboBox()
        self.compress_profile.addItems(["Nagyon jó minőség", "Jó minőség", "Kiegyensúlyozott", "Kis fájlméret", "Maximális tömörítés"])
        self.compress_profile.setToolTip("Minőségi profil a tömörítéshez")
        
        # Target size row with value + unit
        target_row = QWidget()
        target_layout = QHBoxLayout(target_row)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.setSpacing(8)
        
        self.target_value = QDoubleSpinBox()
        self.target_value.setRange(1, 100000)
        self.target_value.setValue(500)
        self.target_value.setDecimals(1)
        self.target_value.setSingleStep(10)
        self.target_value.setToolTip("Cél fájlméret")
        
        self.target_unit = QComboBox()
        self.target_unit.addItems(["MB", "GB"])
        self.target_unit.setFixedWidth(70)
        self.target_unit.setToolTip("Mértékegység")
        
        target_layout.addWidget(self.target_value, 1)
        target_layout.addWidget(self.target_unit)
        
        self.video_bitrate = QSpinBox()
        self.video_bitrate.setRange(100, 200000)
        self.video_bitrate.setValue(2500)
        self.video_bitrate.setSuffix(" kbps")
        self.video_bitrate.setToolTip("Videó bitráta (kbps)")
        
        self.max_bitrate = QSpinBox()
        self.max_bitrate.setRange(100, 300000)
        self.max_bitrate.setValue(4000)
        self.max_bitrate.setSuffix(" kbps")
        self.max_bitrate.setToolTip("Maximális bitráta (kbps)")
        
        self.buffer_size = QSpinBox()
        self.buffer_size.setRange(100, 500000)
        self.buffer_size.setValue(8000)
        self.buffer_size.setSuffix(" kbps")
        self.buffer_size.setToolTip("Puffer méret (kbps) - nagyobb érték = stabilabb bitráta")
        
        self.estimate = QLabel("Célméret számítás: válassz videót.")
        self.estimate.setObjectName("mutedText")
        self.estimate.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #6b7a8e;
                font-size: 12px;
                font-family: "JetBrains Mono", monospace;
                padding: 8px;
                border-radius: 6px;
                background: #0d121a;
                border: 1px solid #1e2a3d;
            }
        """)
        self.estimate.setWordWrap(True)
        
        form.addRow("Tömörítési mód", self.compress_mode)
        form.addRow("Minőségi profil", self.compress_profile)
        form.addRow("Célméret", target_row)
        form.addRow("Videó bitráta", self.video_bitrate)
        form.addRow("Max. bitráta", self.max_bitrate)
        form.addRow("Puffer", self.buffer_size)
        form.addRow("", self.estimate)
        
        layout.addLayout(form)
        
        # Initial visibility update
        self._on_compress_mode_changed(self.compress_mode.currentText())
        
        return group
    
    def _on_compress_mode_changed(self, mode_text: str) -> None:
        is_target_size = mode_text == "Célfájlméret alapján"
        is_bitrate = mode_text == "Egyéni bitráta alapján"
        is_quality = mode_text == "Minőség alapján"
        
        self.target_value.setEnabled(is_target_size)
        self.target_unit.setEnabled(is_target_size)
        self.video_bitrate.setEnabled(is_bitrate)
        self.max_bitrate.setEnabled(is_bitrate)
        self.buffer_size.setEnabled(is_bitrate)
        self.compress_profile.setEnabled(is_quality or is_target_size)
        
        # Update estimate visibility
        self.estimate.setVisible(is_target_size)
        
        if is_target_size:
            self._update_estimate()
    
    def _update_estimate(self) -> None:
        # This will be properly updated when a video is selected
        if hasattr(self, '_last_video_info'):
            self._update_estimate_for_video(self._last_video_info)
    
    def _update_estimate_for_video(self, info: VideoInfo) -> None:
        self._last_video_info = info
        opts = self.options()
        if opts.compression_mode == CompressionMode.TARGET_SIZE:
            try:
                result = calculate_video_bitrate(info.duration_seconds, target_size_to_bytes(opts.target_size_value, opts.target_size_unit), opts.audio_bitrate_kbps)
                saving = max(0, info.size_bytes - result.expected_size_bytes)
                self.estimate.setText(
                    f"Eredeti: {format_file_size(info.size_bytes)}  →  Cél: {format_file_size(result.expected_size_bytes)}  "
                    f"(megtakarítás: {format_file_size(saving)})  |  "
                    f"Videó: {result.video_bitrate_kbps} kbps  |  Hang: {result.audio_bitrate_kbps} kbps"
                )
            except ValueError as e:
                self.estimate.setText(f"Hiba: {str(e)}")
                self.estimate.setStyleSheet(self.estimate.styleSheet().replace("#6b7a8e", "#ff3d5c"))
        elif opts.compression_mode == CompressionMode.BITRATE:
            estimated_size = int((opts.video_bitrate_kbps + opts.audio_bitrate_kbps) * info.duration_seconds * 1000 / 8)
            saving = max(0, info.size_bytes - estimated_size)
            self.estimate.setText(
                f"Eredeti: {format_file_size(info.size_bytes)}  →  Becsült: {format_file_size(estimated_size)}  "
                f"(megtakarítás: {format_file_size(saving)})  |  "
                f"Videó: {opts.video_bitrate_kbps} kbps  |  Hang: {opts.audio_bitrate_kbps} kbps"
            )
        else:
            self.estimate.setText("Minőség-alapú mód: a fájlméret a videó tartalmától függ.")
    
    def show_video_info(self, info: VideoInfo) -> None:
        super().show_video_info(info)
        self._update_estimate_for_video(info)
    
    def options(self) -> ConversionOptions:
        opts = super().options()
        opts.mode = ConversionMode.COMPRESS
        opts.quality_profile = self.compress_profile.currentText()
        opts.target_size_value = float(self.target_value.value())
        opts.target_size_unit = self.target_unit.currentText()
        opts.video_bitrate_kbps = int(self.video_bitrate.value())
        opts.max_bitrate_kbps = int(self.max_bitrate.value())
        opts.buffer_size_kbps = int(self.buffer_size.value())
        mode_map = {
            "Minőség alapján": CompressionMode.QUALITY,
            "Célfájlméret alapján": CompressionMode.TARGET_SIZE,
            "Egyéni bitráta alapján": CompressionMode.BITRATE,
        }
        opts.compression_mode = mode_map[self.compress_mode.currentText()]
        return opts
    
    def make_task(self, info: VideoInfo, output_dir: Path) -> ConversionTask:
        opts = self.options()
        out = ensure_unique_path(output_dir / default_output_name(info.path, "compressed", opts.container))
        return ConversionTask(info, out, opts)