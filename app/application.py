from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from app.core.settings_manager import SettingsManager
from app.ui.main_window import MainWindow
from app.utils.logger import configure_logging


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base.joinpath(*parts)


def create_application(argv: list[str]) -> tuple[QApplication, MainWindow]:
    settings = SettingsManager()
    configure_logging(settings.app_dir / "logs", settings.get().log_level)
    app = QApplication(argv)
    app.setApplicationName("ConvertFlow Desktop")
    app.setOrganizationName("ConvertFlow")
    
    # Set application icon
    icon_path = resource_path("app", "resources", "icons", "app.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    qss = resource_path("app", "resources", "styles", "dark.qss")
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))
    return app, MainWindow(settings)
