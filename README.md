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

## 📦 Folder layout

