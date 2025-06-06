@echo off
REM Clean old artefacts
rmdir /s /q build 2>nul
rmdir /s /q dist  2>nul
del   DiskSweeperGUI.spec 2>nul

REM Re-compile Qt resources (in case icons changed)
.\.venv\Scripts\pyside6-rcc.exe sweeper\gui\resources.qrc -o sweeper\gui\resources_rc.py

REM Build ONEDIR (fast launch) + ONEFILE (single exe)
echo Building onedir…
.\.venv\Scripts\python -m PyInstaller --noconsole --onedir --name DiskSweeperGUI ^
  --add-data "data;data" --icon assets\logo.ico run_gui.py

echo Building onefile…
.\.venv\Scripts\python -m PyInstaller --noconsole --onefile --name DiskSweeperGUI ^
  --add-data "data;data" --icon assets\logo.ico run_gui.py
