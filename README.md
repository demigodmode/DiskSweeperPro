# Disk Sweeper Pro

> A smart, severity-aware disk-cleanup utility with both **CLI** and **PySide 6 GUI**.  
> Designed for Windows 10 / 11.  
> **Nothing is deleted by default** – you decide what goes.

---

## ✨ Features

| Tier      | What it targets                                | Default action |
|-----------|-----------------------------------------------|----------------|
| **Safe**  | Temp folders, browser caches                  | *Selected*     |
| **Moderate** | Prefetch, thumbnail cache, Windows update downloads | *Selected*     |
| **Aggressive** | WinSxS (aged files) & other rollback data | *Unselected*   |

* Clear explanations of the risk (“first launch slower”, “no rollback”).
* GUI progress dialog with **Abort** button.
* Console **✓ lines** and final “≈ Freed X GB” summary.
* Log of every sweep under `%LOCALAPPDATA%\DiskSweeper\logs`.

---

## 🛠 Installation

```bash
# clone → enter → create isolated env
git clone https://github.com/demigodmode/DiskSweeperPro.git
cd DiskSweeperPro
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## 🚀 Usage

### CLI (review / clean)

```bash
python -m sweeper.cli       # same as "report"
python -m sweeper.cli clean # delete safe + moderate
python -m sweeper.cli deep  # delete ALL severities
```

### GUI

```bash
python run_gui.py           # fast when launched from source
# or the packaged EXE (onedir build):
dist\DiskSweeperGUI\DiskSweeperGUI.exe
```

## 🏗 Build (optional)

```bash
scripts\build_exe.bat   # one-liner: cleans → onedir → onefile
```

## 📦 Folder layout

- `assets/`   SVG / ICO icons
- `data/`     YAML rule presets
- `scripts/`  helper scripts (e.g. `build_exe.bat`)
- `sweeper/`  package source
  - `cli/`     command-line interface
  - `core/`    rule engine + helpers
  - `gui/`     PySide 6 front-end
- `tests/`    pytest unit tests
- `run_gui.py` one-line wrapper that launches the GUI (used by PyInstaller)

## 🤝 Contributing

1. Fork / clone
2. `pip install -r requirements.txt`
3. Run `pytest -q` & `python run_gui.py` to verify
4. Create a feature branch (`git checkout -b feat/your-feature`)
5. Open a pull request 🎉

