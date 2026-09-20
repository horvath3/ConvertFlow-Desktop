import sys
import os
from pathlib import Path
from io import BytesIO

from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtCore import Qt, QBuffer, QIODevice
from PIL import Image

# Initialize QApplication (needed for Qt GUI operations)
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

svg_path = Path('app/resources/icons/logo.svg')
ico_path = Path('app/resources/icons/app.ico')

sizes = [16, 24, 32, 48, 64, 128, 256]

renderer = QSvgRenderer(str(svg_path))
if not renderer.isValid():
    print("ERROR: Invalid SVG")
    sys.exit(1)

images = []
for size in sizes:
    # Create a transparent image
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    
    # Render SVG to image
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()
    
    # Convert QImage to PIL Image via QPixmap -> QBuffer -> bytes
    pixmap = QPixmap.fromImage(image)
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    
    # Convert QByteArray to bytes for PIL
    png_bytes = bytes(buffer.data())
    buffer.close()
    
    # Load with PIL
    pil_image = Image.open(BytesIO(png_bytes))
    pil_image.load()  # Force load
    images.append(pil_image.copy())
    print(f'Rendered {size}x{size}')

# Save as ICO
images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in images])
print(f'Created {ico_path}')

# Also create a PNG for the logo
png_path = Path('app/resources/icons/logo.png')
images[-1].save(png_path, format='PNG')
print(f'Created {png_path}')