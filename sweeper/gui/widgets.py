from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QPainter
from PySide6.QtWidgets import QStyledItemDelegate

_SEV = {
    "safe":       QColor("#4CAF50"),   # green
    "moderate":   QColor("#FF9800"),   # orange
    "aggressive": QColor("#F44336"),   # red
}

class SeverityBadge(QStyledItemDelegate):
    """Paint severity text in colour."""
    def paint(self, painter: QPainter, opt, idx):
        sev = idx.data()
        painter.save()
        painter.setPen(_SEV.get(sev, opt.palette.color(QPalette.Text)))
        painter.drawText(opt.rect, Qt.AlignCenter, sev)
        painter.restore()

class SizeAlignDelegate(QStyledItemDelegate):
    """Right-align numeric size column."""
    def initStyleOption(self, opt, idx):
        super().initStyleOption(opt, idx)
        opt.displayAlignment = Qt.AlignRight | Qt.AlignVCenter
