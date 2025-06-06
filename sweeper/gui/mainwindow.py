#!/usr/bin/env python3
"""
Disk Sweeper Pro – GUI main window
* Icons + full menu bar
* Dark/Light toggle, rule reload, log-folder opener, CSV export
"""

from __future__ import annotations
import ctypes
from importlib import reload
from pathlib import Path

from PySide6.QtCore import Qt, QModelIndex, Slot, QUrl
from PySide6.QtGui import QIcon, QKeySequence, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QAbstractItemView, QPushButton, QLabel, QMessageBox,
    QProgressDialog, QFileDialog
)

import sweeper.gui.resources_rc  # compiled RCC icons
from .widgets import SeverityBadge, SizeAlignDelegate
from ..core.collector import collect, fmt_sz
from ..core.cleaner import clean
from ..core import rules as rules_mod  # for reload
from ..core.rules import Candidate, SEVERITY_ORDER, LOCAL

from PySide6.QtCore import QAbstractTableModel


# ── Table model -------------------------------------------------------------
class CandidateModel(QAbstractTableModel):
    HEADERS = ["✔", "Label", "Size", "Severity", "Reason"]

    def __init__(self, rows: list[Candidate]):
        super().__init__()
        self._rows = rows
        self._checked = [False] * len(rows)

    # Qt basics
    def rowCount(self, *_): return len(self._rows)
    def columnCount(self, *_): return len(self.HEADERS)
    def headerData(self, s, orient, role):
        if orient == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[s]

    def flags(self, idx):
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return base | Qt.ItemIsUserCheckable if idx.column() == 0 else base

    def data(self, idx: QModelIndex, role):
        r, c = idx.row(), idx.column()
        cand = self._rows[r]
        if c == 0 and role == Qt.CheckStateRole:
            return Qt.Checked if self._checked[r] else Qt.Unchecked
        if role != Qt.DisplayRole:
            return None
        return (cand.rule.label,
                fmt_sz(cand.size),
                cand.rule.severity,
                cand.rule.reason)[c - 1]

    def setData(self, idx: QModelIndex, value, role):
        if idx.column() == 0 and role == Qt.CheckStateRole:
            self._checked[idx.row()] = (value == Qt.Checked)
            self.dataChanged.emit(idx, idx)
            return True
        return False

    # sorting
    def sort(self, column, order):
        rev = order == Qt.DescendingOrder
        def key(c: Candidate):
            return (c.rule.label, c.size,
                    SEVERITY_ORDER[c.rule.severity], c.rule.reason)[column-1] if column else 0
        self.beginResetModel()
        self._rows.sort(key=key, reverse=rev)
        self._checked = [False]*len(self._rows)
        self.endResetModel()

    # helpers
    def toggle_all(self, state: bool):
        self._checked = [state]*len(self._checked)
        self.dataChanged.emit(self.index(0,0), self.index(len(self._rows)-1,0))
    def invert(self):
        self._checked = [not x for x in self._checked]
        self.dataChanged.emit(self.index(0,0), self.index(len(self._rows)-1,0))
    def selected(self): return [c for c,ck in zip(self._rows,self._checked) if ck]


# ── Main window -------------------------------------------------------------
class MainWindow(QMainWindow):
    VERSION = "0.4.3"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Disk Sweeper Pro")
        self.setWindowIcon(QIcon(":/icons/logo"))
        QApplication.setStyle("Fusion")

        # model & table
        self._rebuild_model()

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setColumnWidth(0, 30)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setItemDelegateForColumn(2, SizeAlignDelegate(self.table))
        self.table.setItemDelegateForColumn(3, SeverityBadge(self.table))
        self.table.clicked.connect(self._row_toggle)

        # bottom bar
        self.lbl = QLabel(self._space())
        btn_sel = QPushButton("Select All")
        btn_sel.clicked.connect(lambda: (self.model.toggle_all(True), self._update()))
        btn_inv = QPushButton("Invert")
        btn_inv.clicked.connect(lambda: (self.model.invert(), self._update()))
        btn_clean = QPushButton("  CLEAN")
        btn_clean.setIcon(QIcon(":/icons/broom"))
        btn_clean.clicked.connect(self._clean)

        bar = QHBoxLayout()
        bar.addWidget(self.lbl)
        bar.addStretch(1)
        bar.addWidget(btn_sel)
        bar.addWidget(btn_inv)
        bar.addWidget(btn_clean)

        # central widget
        central = QWidget(self)
        lay = QVBoxLayout(central)
        lay.addWidget(self.table)
        lay.addLayout(bar)
        self.setCentralWidget(central)

        self.dark = True
        try:
            import qdarkstyle
            QApplication.instance().setStyleSheet(qdarkstyle.load_stylesheet())
        except ImportError:
            self.dark = False

        # menus
        self._build_menus()

    # ----- menu bar --------------------------------------------------------
    def _build_menus(self):
        mbar = self.menuBar()

        # FILE
        filem = mbar.addMenu("&File")
        act_reload = filem.addAction("Reload &Rules")
        act_reload.setShortcut(QKeySequence.Refresh)
        act_reload.triggered.connect(self._reload_rules)
        filem.addSeparator()
        act_exit = filem.addAction("E&xit")
        act_exit.setShortcut(QKeySequence.Quit)
        act_exit.triggered.connect(QApplication.quit)

        # VIEW
        view = mbar.addMenu("&View")
        act_theme = view.addAction("Toggle Dark / Light")
        act_theme.triggered.connect(self._toggle_theme)

        # TOOLS
        tools = mbar.addMenu("&Tools")
        act_logs = tools.addAction("Open &Log Folder")
        act_logs.triggered.connect(self._open_logs)
        act_csv = tools.addAction("&Export Report…")
        act_csv.triggered.connect(self._export_csv)

        # HELP
        helpm = mbar.addMenu("&Help")
        helpm.addAction("&GitHub Project",
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/YourUser/DiskSweeperPro")))
        helpm.addSeparator()
        helpm.addAction("&About…", self._about)

    # ----- slots / helpers -------------------------------------------------
    def _rebuild_model(self):
        rows = collect(rules_mod.RULES, include=set(rules_mod.SEVERITY_ORDER))
        rows.sort(key=lambda c: (rules_mod.SEVERITY_ORDER[c.rule.severity], -c.size))
        self.model = CandidateModel(rows)

    @Slot()
    def _reload_rules(self):
        try:
            reload(rules_mod)
            self._rebuild_model()
            self.table.setModel(self.model)
            self._update()
            QMessageBox.information(self, "Rules reloaded", "Rule list reloaded from YAML / source.")
        except Exception as exc:
            QMessageBox.critical(self, "Error reloading rules", str(exc))

    @Slot()
    def _toggle_theme(self):
        try:
            import qdarkstyle
        except ImportError:
            return
        if self.dark:
            QApplication.instance().setStyleSheet("")
        else:
            QApplication.instance().setStyleSheet(qdarkstyle.load_stylesheet())
        self.dark = not self.dark

    @Slot()
    def _open_logs(self):
        target = (LOCAL / "DiskSweeper" / "logs").resolve()
        target.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    @Slot()
    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export report", "sweep_report.csv", "CSV files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("Label,Size,Severity,Path\n")
                for c in self.model._rows:
                    fh.write(f"{c.rule.label},{c.size},{c.rule.severity},\"{c.path}\"\n")
            QMessageBox.information(self, "Export complete", "CSV saved.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _space(self): return f"Potential space: {fmt_sz(sum(c.size for c in self.model.selected()))}"
    def _update(self): self.lbl.setText(self._space())

    @Slot(QModelIndex)
    def _row_toggle(self, idx: QModelIndex):
        chk = self.model.index(idx.row(), 0)
        cur = self.model.data(chk, Qt.CheckStateRole)
        self.model.setData(chk, Qt.Unchecked if cur == Qt.Checked else Qt.Checked, Qt.CheckStateRole)
        self._update()

    @Slot()
    def _clean(self):
        sel = self.model.selected()
        if not sel:
            QMessageBox.information(self, "Disk Sweeper", "Nothing selected.")
            return
        if any("WinSxS" in str(c.path) for c in sel) and not ctypes.windll.shell32.IsUserAnAdmin():
            QMessageBox.warning(self, "Warning",
                "WinSxS cleanup may remove rollback files.\nRun as Admin for full access.")
        if QMessageBox.question(
            self, "Confirm delete", f"Delete {len(sel)} item(s)?",
            QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        dlg = QProgressDialog("Cleaning…", "Abort", 0, len(sel), self)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.show()
        for i, cand in enumerate(sel, 1):
            clean([cand], echo=True)
            dlg.setValue(i)
            QApplication.processEvents()
            if dlg.wasCanceled():
                break
        dlg.close()
        QMessageBox.information(self, "Disk Sweeper", "Cleanup done.")
        self.close()

    def _about(self):
        QMessageBox.about(
            self, "About Disk Sweeper Pro",
            f"<h3>Disk Sweeper Pro</h3>"
            f"<img src=':/icons/logo' width='64' height='64'><br>"
            f"Version {self.VERSION}<br>"
            f"Smart, severity-aware disk cleanup.<br>"
            f"© @DemiGodMode 2025"
        )
