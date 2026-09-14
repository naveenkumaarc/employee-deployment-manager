from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRectF, Qt
from PySide6.QtGui import (\n    QBrush, QColor, QIcon, QImage, QLinearGradient, QPainter, QPainterPath, QPen\n)

APP_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<defs>
  <linearGradient id="tile" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#243B70"/>
    <stop offset="1" stop-color="#112445"/>
  </linearGradient>
  <linearGradient id="blue" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#6B82FF"/>
    <stop offset="1" stop-color="#425DDB"/>
  </linearGradient>
</defs>
<rect x="28" y="28" width="456" height="456" rx="132" fill="url(#tile)"/>
<rect x="104" y="112" width="304" height="270" rx="42" fill="#F8FAFF"/>
<path d="M104 154c0-23 19-42 42-42h220c23 0 42 19 42 42v49H104z" fill="url(#blue)"/>
<rect x="152" y="82" width="30" height="72" rx="15" fill="#172B53"/>
<rect x="330" y="82" width="30" height="72" rx="15" fill="#172B53"/>
<g fill="#CFD8EA">
  <rect x="146" y="236" width="54" height="42" rx="10"/>
  <rect x="222" y="236" width="54" height="42" rx="10"/>
  <rect x="298" y="236" width="54" height="42" rx="10"/>
  <rect x="222" y="298" width="54" height="42" rx="10"/>
  <rect x="298" y="298" width="54" height="42" rx="10"/>
</g>
<circle cx="148" cy="320" r="39" fill="#EDF2FC"/>
<path d="M79 408c0-48 31-82 69-82s69 34 69 82c0 15-138 15-138 0z" fill="#6B82FF"/>
<path d="M365 258c-48 0-87 39-87 87 0 66 87 132 87 132s87-66 87-132c0-48-39-87-87-87z" fill="#FF6B6B"/>
<circle cx="365" cy="344" r="48" fill="#FFF"/>
<path d="M338 345l18 18 37-42" fill="none" stroke="#FF5B5B" stroke-width="17" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / relative


def _draw_icon(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scale = size / 512.0
    painter.scale(scale, scale)

    tile = QPainterPath()
    tile.addRoundedRect(QRectF(28, 28, 456, 456), 132, 132)
    tile_gradient = QLinearGradient(28, 28, 484, 484)
    tile_gradient.setColorAt(0, QColor("#243B70"))
    tile_gradient.setColorAt(1, QColor("#112445"))
    painter.fillPath(tile, QBrush(tile_gradient))

    calendar = QPainterPath()
    calendar.addRoundedRect(QRectF(104, 112, 304, 270), 42, 42)
    painter.fillPath(calendar, QColor("#F8FAFF"))
    painter.setClipPath(calendar)
    header_gradient = QLinearGradient(104, 112, 408, 203)
    header_gradient.setColorAt(0, QColor("#6B82FF"))
    header_gradient.setColorAt(1, QColor("#425DDB"))
    painter.fillRect(QRectF(104, 112, 304, 91), QBrush(header_gradient))
    painter.setClipping(False)

    for x in (152, 330):
        ring = QPainterPath()
        ring.addRoundedRect(QRectF(x, 82, 30, 72), 15, 15)
        painter.fillPath(ring, QColor("#172B53"))

    painter.setPen(QPen(QColor("#CFD8EA"), 1))
    painter.setBrush(QColor("#CFD8EA"))
    for x, y in ((146, 236), (222, 236), (298, 236), (222, 298), (298, 298)):
        painter.drawRoundedRect(QRectF(x, y, 54, 42), 10, 10)

    painter.setPen(QPen(QColor("#EDF2FC"), 1))
    painter.setBrush(QColor("#EDF2FC"))
    painter.drawEllipse(QRectF(109, 281, 78, 78))
    body = QPainterPath()
    body.moveTo(79, 408)
    body.cubicTo(79, 360, 110, 326, 148, 326)
    body.cubicTo(186, 326, 217, 360, 217, 408)
    body.cubicTo(217, 423, 79, 423, 79, 408)
    painter.fillPath(body, QColor("#6B82FF"))

    pin = QPainterPath()
    pin.moveTo(365, 258)
    pin.cubicTo(317, 258, 278, 297, 278, 345)
    pin.cubicTo(278, 411, 365, 477, 365, 477)
    pin.cubicTo(365, 477, 452, 411, 452, 345)
    pin.cubicTo(452, 297, 413, 258, 365, 258)
    painter.fillPath(pin, QColor("#FF6B6B"))
    painter.setBrush(QColor("#FFFFFF"))
    painter.setPen(QPen(QColor("#FFFFFF"), 1))
    painter.drawEllipse(QRectF(317, 296, 96, 96))
    check_pen = QPen(QColor("#FF5B5B"), 17)
    check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(check_pen)
    painter.drawLine(338, 345, 356, 363)
    painter.drawLine(356, 363, 393, 321)
    painter.end()
    return image


def _png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def write_icon_assets(
    directory: str | Path, *, overwrite: bool = False
) -> tuple[Path, Path]:
    """Create alpha-safe PNG and multi-size ICO assets."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    png_path = target / "app_icon.png"
    ico_path = target / "app_icon.ico"

    if overwrite or not png_path.exists():
        _draw_icon(512).save(str(png_path), "PNG")

    if overwrite or not ico_path.exists():
        sizes = (16, 24, 32, 48, 64, 128, 256)
        payloads = [_png_bytes(_draw_icon(size)) for size in sizes]
        header = struct.pack("<HHH", 0, 1, len(sizes))
        offset = 6 + (16 * len(sizes))
        entries = []
        for size, payload in zip(sizes, payloads):
            dimension = 0 if size == 256 else size
            entries.append(
                struct.pack(
                    "<BBBBHHII",
                    dimension,
                    dimension,
                    0,
                    0,
                    1,
                    32,
                    len(payload),
                    offset,
                )
            )
            offset += len(payload)
        ico_path.write_bytes(header + b"".join(entries) + b"".join(payloads))

    return png_path, ico_path


def app_icon() -> QIcon:
    png = resource_path("assets/app_icon.png")
    if png.exists():
        return QIcon(str(png))
    generated, _ = write_icon_assets(
        Path.home() / ".deployment_desk" / "assets"
    )
    return QIcon(str(generated))
