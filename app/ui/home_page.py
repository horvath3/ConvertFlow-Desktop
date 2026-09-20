from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget, QSizePolicy, QScrollArea
)
from PySide6.QtGui import QPixmap, QIcon, QColor

from app.core.ffmpeg_manager import FFmpegManager
from app.core.hardware_detection import HardwareStatus
from app.core.settings_manager import AppSettings
from app.utils.format_utils import format_file_size


def _render_svg_icon(svg: str, color: str, size: int = 24) -> QPixmap:
    """Render SVG icon with explicit color replacement."""
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtGui import QPainter
    
    # Replace currentColor with actual color
    svg_colored = svg.replace('currentColor', color)
    
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    renderer = QSvgRenderer(svg_colored.encode())
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()
    
    return pixmap


class StatCard(QFrame):
    """Animated stat card for dashboard."""
    
    def __init__(self, title: str, value: str, icon_svg: str, accent_color: str = "#5b7cfa", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setFixedHeight(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._accent_color = accent_color
        self._target_value = value
        self._current_value = "0"
        
        # Main card styling
        self.setStyleSheet(f"""
            #statCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #111820, stop:1 #0d121a);
                border: 1px solid #233044;
                border-radius: 12px;
                border-left: 3px solid {accent_color};
            }}
            #statCard:hover {{
                border-color: {accent_color};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #151e2d, stop:1 #111820);
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)
        
        # Icon container
        icon_container = QFrame()
        icon_container.setFixedSize(44, 44)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {accent_color}33, stop:1 {accent_color}1a);
                border: 1px solid {accent_color}55;
                border-radius: 10px;
            }}
        """)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Render icon with accent color
        pixmap = _render_svg_icon(icon_svg, accent_color, 24)
        icon_label.setPixmap(pixmap)
        icon_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon_container)
        
        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.value_label = QLabel(self._current_value)
        self.value_label.setObjectName("statValue")
        self.value_label.setStyleSheet("""
            QLabel {
                font-size: 26px;
                font-weight: 700;
                color: #f0f4fa;
                background: transparent;
            }
        """)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("statTitle")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: 600;
                color: #9ca8b8;
                background: transparent;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)
        
        text_layout.addWidget(self.value_label)
        text_layout.addWidget(self.title_label)
        text_layout.addStretch()
        layout.addLayout(text_layout)
        layout.addStretch()
    
    def animate_value(self, new_value: str) -> None:
        """Animate the value change (simplified)."""
        self.value_label.setText(new_value)


class ActionCard(QPushButton):
    """Large action card for main actions."""
    
    def __init__(self, title: str, description: str, icon_svg: str, accent_color: str = "#5b7cfa", parent=None):
        super().__init__(parent)
        self.setObjectName("actionCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._accent_color = accent_color
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel()
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Render icon with accent color
        pixmap = _render_svg_icon(icon_svg, accent_color, 36)
        icon_label.setPixmap(pixmap)
        
        # Title
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 700;
                color: #f0f4fa;
                background: transparent;
            }
        """)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #9ca8b8;
                background: transparent;
                line-height: 1.5;
            }
        """)
        
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch(1)
        
        # Hover effect via stylesheet
        self.setStyleSheet(f"""
            #actionCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #111820, stop:1 #0d121a);
                border: 1px solid #1e2a3d;
                border-radius: 14px;
                border-left: 3px solid {accent_color};
                text-align: left;
                padding: 0px;
            }}
            #actionCard:hover {{
                border-color: {accent_color};
                border-left: 3px solid {accent_color};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #151e2d, stop:1 #111820);
            }}
            #actionCard:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0d121a, stop:1 #0a0e14);
            }}
        """)


class HomePage(QWidget):
    def __init__(self, ffmpeg: FFmpegManager, settings: AppSettings, hardware: HardwareStatus) -> None:
        super().__init__()
        self.ffmpeg = ffmpeg
        self.settings = settings
        self.hardware = hardware
        self.active = 0
        self.waiting = 0
        
        self._build()
        self.refresh()
    
    def _build(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ===== SCROLL AREA =====
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: #233044;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #354864;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(32, 28, 32, 28)
        content_layout.setSpacing(28)
        
        # ===== HEADER =====
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)
        
        # Title section
        title_layout = QVBoxLayout()
        title_layout.setSpacing(6)
        
        title = QLabel("ConvertFlow Desktop")
        title.setObjectName("pageTitle")
        title.setStyleSheet("""
            QLabel {
                font-size: 30px;
                font-weight: 700;
                color: #f0f4fa;
                letter-spacing: -0.5px;
            }
        """)
        
        subtitle = QLabel("Offline videókonvertálás és tömörítés Windowsra")
        subtitle.setObjectName("mutedText")
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #9ca8b8;
                font-weight: 400;
            }
        """)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Quick action button
        quick_convert = QPushButton("Új konverzió")
        quick_convert.setObjectName("quickActionBtn")
        quick_convert.setProperty("primary", True)
        quick_convert.setFixedHeight(44)
        quick_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(quick_convert)
        
        content_layout.addWidget(header)
        
        # ===== FFMPEG WARNING =====
        self.ffmpeg_notice = QFrame()
        self.ffmpeg_notice.setObjectName("warningPanel")
        self.ffmpeg_notice.setVisible(False)
        notice_layout = QHBoxLayout(self.ffmpeg_notice)
        notice_layout.setContentsMargins(16, 12, 16, 12)
        notice_layout.setSpacing(12)
        
        # Warning icon
        warn_icon = QLabel()
        warn_icon.setFixedSize(24, 24)
        warn_pixmap = _render_svg_icon(
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffd600" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
            "#ffd600", 24
        )
        warn_icon.setPixmap(warn_pixmap)
        notice_layout.addWidget(warn_icon)
        
        notice_text_layout = QVBoxLayout()
        notice_text_layout.setSpacing(2)
        
        self.ffmpeg_notice_title = QLabel("FFmpeg nincs beállítva")
        self.ffmpeg_notice_title.setObjectName("warningTitle")
        self.ffmpeg_notice_title.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #ffd600;
                font-size: 14px;
                font-weight: 700;
            }
        """)
        
        self.ffmpeg_notice_text = QLabel()
        self.ffmpeg_notice_text.setWordWrap(True)
        self.ffmpeg_notice_text.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #d4b870;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        notice_text_layout.addWidget(self.ffmpeg_notice_title)
        notice_text_layout.addWidget(self.ffmpeg_notice_text)
        notice_layout.addLayout(notice_text_layout, 1)
        
        # Fix button
        self.fix_ffmpeg_btn = QPushButton("FFmpeg beállítása")
        self.fix_ffmpeg_btn.setProperty("ghost", True)
        self.fix_ffmpeg_btn.setFixedHeight(36)
        self.fix_ffmpeg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        notice_layout.addWidget(self.fix_ffmpeg_btn)
        
        content_layout.addWidget(self.ffmpeg_notice)
        
        # ===== STATS ROW =====
        stats_container = QWidget()
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(16)
        
        # Stat cards
        self.stat_active = StatCard("Aktív feladatok", "0", self._icon_activity(), "#5b7cfa")
        self.stat_waiting = StatCard("Várakozó", "0", self._icon_clock(), "#00d4ff")
        self.stat_completed = StatCard("Kész", "0", self._icon_check(), "#00e676")
        self.stat_space = StatCard("Elérhető hely", "...", self._icon_drive(), "#ffd600")
        
        stats_layout.addWidget(self.stat_active)
        stats_layout.addWidget(self.stat_waiting)
        stats_layout.addWidget(self.stat_completed)
        stats_layout.addWidget(self.stat_space)
        
        content_layout.addWidget(stats_container)
        
        # ===== MAIN ACTIONS GRID =====
        actions_label = QLabel("Gyors műveletek")
        actions_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 600;
                color: #9ca8b8;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 8px 0 4px 0;
            }
        """)
        content_layout.addWidget(actions_label)
        
        actions_grid = QGridLayout()
        actions_grid.setSpacing(16)
        # Ensure rows expand to fill available space and have minimum height
        actions_grid.setRowStretch(0, 1)
        actions_grid.setRowStretch(1, 1)
        actions_grid.setRowMinimumHeight(0, 140)
        actions_grid.setRowMinimumHeight(1, 140)
        
        self.action_convert = ActionCard(
            "Videó konvertálása",
            "Formátumváltás, kodek-választás,\nfelbontás és FPS módosítás",
            self._icon_convert(), "#5b7cfa"
        )
        
        self.action_compress = ActionCard(
            "Videó tömörítése",
            "Célméret megadása, minőségi profilok,\nkétmenetes kódolás támogatása",
            self._icon_compress(), "#00d4ff"
        )
        
        self.action_history = ActionCard(
            "Konverziós előzmények",
            "Előző feladatok megtekintése,\nújraindítás, kimeneti mappa megnyitása",
            self._icon_history(), "#7c4dff"
        )
        
        self.action_settings = ActionCard(
            "Beállítások",
            "Alapértelmezett kódolók, teljesítmény\nmódok, kimeneti mappa, NVENC",
            self._icon_settings(), "#ffd600"
        )
        
        actions_grid.addWidget(self.action_convert, 0, 0)
        actions_grid.addWidget(self.action_compress, 0, 1)
        actions_grid.addWidget(self.action_history, 1, 0)
        actions_grid.addWidget(self.action_settings, 1, 1)
        
        content_layout.addLayout(actions_grid)
        
        # ===== SYSTEM STATUS =====
        status_label = QLabel("Rendszerállapot")
        status_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 600;
                color: #9ca8b8;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 8px 0 4px 0;
            }
        """)
        content_layout.addWidget(status_label)
        
        self.status_card = QFrame()
        self.status_card.setObjectName("statusCard")
        self.status_card.setStyleSheet("""
            #statusCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #111820, stop:1 #0d121a);
                border: 1px solid #233044;
                border-radius: 12px;
            }
        """)
        status_layout = QVBoxLayout(self.status_card)
        status_layout.setContentsMargins(20, 16, 20, 16)
        status_layout.setSpacing(10)
        
        self.status_grid = QGridLayout()
        self.status_grid.setSpacing(12)
        self.status_grid.setColumnStretch(1, 1)
        self.status_grid.setColumnStretch(3, 1)
        
        status_layout.addLayout(self.status_grid)
        
        # Refresh button
        refresh_btn = QPushButton("Frissítés")
        refresh_btn.setProperty("ghost", True)
        refresh_btn.setFixedHeight(36)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        status_layout.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        content_layout.addWidget(self.status_card)
        content_layout.addStretch()
        
        # Set content widget in scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        # Connect signals
        self.action_convert.clicked.connect(lambda: self._navigate_to(1))
        self.action_compress.clicked.connect(lambda: self._navigate_to(2))
        self.action_settings.clicked.connect(lambda: self._navigate_to(3))
        quick_convert.clicked.connect(lambda: self._navigate_to(1))
        
        # Auto-refresh timer for disk space
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._update_disk_space)
        self._refresh_timer.start(10000)  # Every 10 seconds
    
    def _navigate_to(self, index: int) -> None:
        window = self.window()
        if hasattr(window, '_switch_page'):
            window._switch_page(index)
    
    # Icon definitions with proper stroke colors
    def _icon_activity(self) -> str:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>'
    
    def _icon_clock(self) -> str:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
    
    def _icon_check(self) -> str:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
    
    def _icon_drive(self) -> str:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="12" x2="2" y2="12"></line><path d="M5.45 5.11L2 12l3.45 6.89"></path><path d="M18.55 5.11L22 12l-3.45 6.89"></path></svg>'
    
    def _icon_convert(self) -> str:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 16a4 4 0 0 1-4-4V5a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v7a4 4 0 0 1-4 4H7z"></path><line x1="12" y1="2" x2="12" y2="22"></line><path d="M7 12h10"></path></svg>'
    
    def _icon_compress(self) -> str:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>'
    
    def _icon_history(self) -> str:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline><path d="M12 6V6.01"></path></svg>'
    
    def _icon_settings(self) -> str:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'
    
    def set_counts(self, active: int, waiting: int) -> None:
        self.active = active
        self.waiting = waiting
        self.stat_active.animate_value(str(active))
        self.stat_waiting.animate_value(str(waiting))
        self._update_status_grid()
    
    def refresh(self) -> None:
        ffmpeg_ok = self.ffmpeg.ffmpeg_path.exists()
        ffprobe_ok = self.ffmpeg.ffprobe_path.exists()
        nvenc = self.hardware.any_nvenc
        missing_tools = not (ffmpeg_ok and ffprobe_ok)
        
        self.ffmpeg_notice.setVisible(missing_tools)
        if missing_tools:
            self.ffmpeg_notice_title.setText("FFmpeg nincs beállítva")
            self.ffmpeg_notice_text.setText(
                "A konvertáláshoz másold be az ffmpeg.exe és ffprobe.exe fájlokat ide: "
                f"{self.ffmpeg.bundled_dir}. Addig a program elindul, de videót elemezni vagy konvertálni nem tud."
            )
        
        self._update_status_grid()
        self._update_disk_space()
    
    def _update_status_grid(self) -> None:
        # Clear grid
        while self.status_grid.count():
            item = self.status_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Status items
        items = [
            ("FFmpeg", "elérhető" if self.ffmpeg.ffmpeg_path.exists() else "hiányzik", "#00e676" if self.ffmpeg.ffmpeg_path.exists() else "#ff3d5c"),
            ("ffprobe", "elérhető" if self.ffmpeg.ffprobe_path.exists() else "hiányzik", "#00e676" if self.ffmpeg.ffprobe_path.exists() else "#ff3d5c"),
            ("NVIDIA NVENC", "elérhető" if self.hardware.any_nvenc else "nem elérhető", "#00e676" if self.hardware.any_nvenc else "#6b7a8e"),
            ("Alapértelmezett kimeneti mappa", Path(self.settings.default_output_dir).name, "#9ca8b8"),
            ("Teljesítmény mód", self.settings.performance_mode, "#9ca8b8"),
            ("Párhuzamos feladatok", str(self.settings.parallel_jobs), "#9ca8b8"),
            ("Aktív feladatok", str(self.active), "#5b7cfa"),
            ("Várakozó feladatok", str(self.waiting), "#00d4ff"),
        ]
        
        for row, (label, value, color) in enumerate(items):
            lbl = QLabel(label)
            lbl.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #6b7a8e;
                    background: transparent;
                }
            """)
            
            val = QLabel(value)
            val.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    font-weight: 600;
                    color: {color};
                    background: transparent;
                }}
            """)
            
            self.status_grid.addWidget(lbl, row, 0)
            self.status_grid.addWidget(val, row, 1)
            
            if row < len(items) - 1 and row % 2 == 1:
                # Add spacer
                pass
    
    def _update_disk_space(self) -> None:
        import shutil
        try:
            output_path = Path(self.settings.default_output_dir)
            if output_path.exists():
                free_bytes = shutil.disk_usage(output_path).free
                self.stat_space.animate_value(format_file_size(free_bytes))
        except Exception:
            pass