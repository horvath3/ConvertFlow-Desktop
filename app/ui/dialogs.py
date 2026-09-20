from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QPlainTextEdit, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class DetailsDialog(QDialog):
    def __init__(self, title: str, text: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 500)
        self.setMinimumSize(600, 400)
        self.setStyleSheet("""
            QDialog {
                background: #0a0e14;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #f0f4fa;
                background: transparent;
            }
        """)
        layout.addWidget(title_label)
        
        # Text area
        box = QPlainTextEdit(text)
        box.setReadOnly(True)
        box.setStyleSheet("""
            QPlainTextEdit {
                background: #0d121a;
                border: 1px solid #233044;
                border-radius: 10px;
                color: #f0f4fa;
                font-family: "JetBrains Mono", "Consolas", monospace;
                font-size: 12px;
                padding: 12px;
            }
        """)
        layout.addWidget(box, 1)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.setStyleSheet("""
            QDialogButtonBox {
                background: transparent;
            }
            QPushButton {
                min-width: 100px;
                padding: 8px 20px;
            }
        """)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, alignment=Qt.AlignmentFlag.AlignRight)


class ErrorDialog(QDialog):
    """Modern error dialog with better UX."""
    
    def __init__(self, title: str, message: str, details: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog {
                background: #0a0e14;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Icon + Message
        msg_layout = QHBoxLayout()
        msg_layout.setSpacing(16)
        
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setStyleSheet("""
            QLabel {
                background: #ff3d5c22;
                border-radius: 16px;
                color: #ff3d5c;
            }
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setText("⚠")
        icon_label.setFont(icon_label.font())
        
        msg_text = QLabel(message)
        msg_text.setWordWrap(True)
        msg_text.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #f0f4fa;
                background: transparent;
            }
        """)
        
        msg_layout.addWidget(icon_label)
        msg_layout.addWidget(msg_text, 1)
        layout.addLayout(msg_layout)
        
        # Details (collapsible)
        if details:
            details_box = QPlainTextEdit(details)
            details_box.setReadOnly(True)
            details_box.setMaximumHeight(150)
            details_box.setStyleSheet("""
                QPlainTextEdit {
                    background: #0d121a;
                    border: 1px solid #233044;
                    border-radius: 8px;
                    color: #9ca8b8;
                    font-family: "JetBrains Mono", monospace;
                    font-size: 11px;
                    padding: 10px;
                }
            """)
            layout.addWidget(details_box)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.setStyleSheet("""
            QPushButton {
                min-width: 100px;
                padding: 10px 24px;
            }
        """)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons, alignment=Qt.AlignmentFlag.AlignRight)