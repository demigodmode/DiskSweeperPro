use anyhow::Result;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::Path;

use crate::output::fmt_size;
use crate::rules::Candidate;

fn delete_path(path: &Path) -> Result<()> {
    if !path.exists() {
        return Ok(());
    }

    if path.is_dir() {
        fs::remove_dir_all(path)?;
    } else {
        fs::remove_file(path)?;
    }

    Ok(())
}

fn get_log_path() -> Option<std::path::PathBuf> {
    dirs::data_local_dir().map(|local| local.join("DiskSweeper").join("logs").join("sweeps.log"))
}

fn log_sweep(freed: u64) {
    if let Some(log_path) = get_log_path() {
        if let Some(parent) = log_path.parent() {
            let _ = fs::create_dir_all(parent);
        }

        if let Ok(mut file) = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&log_path)
        {
            let timestamp = chrono::Local::now().format("%Y-%m-%d %H:%M");
            let _ = writeln!(file, "{} – freed {} (rust-cli)", timestamp, fmt_size(freed));
        }
    }
}

pub struct CleanResult {
    pub freed: u64,
    pub deleted: usize,
    pub failed: usize,
}

/// Delete candidates and return total freed bytes
pub fn clean(candidates: &[Candidate], echo: bool, dry_run: bool) -> CleanResult {
    use colored::Colorize;

    let mut freed: u64 = 0;
    let mut deleted = 0;
    let mut failed = 0;

    for c in candidates {
        if dry_run {
            if echo {
                println!(
                    "{} {:>9} {}",
                    "[DRY]".yellow(),
                    fmt_size(c.size),
                    c.path.display()
                );
            }
            freed += c.size;
            deleted += 1;
        } else {
            match delete_path(&c.path) {
                Ok(_) => {
                    freed += c.size;
                    deleted += 1;
                    if echo {
                        println!(
                            "{} {:>9} {}",
                            "✓".green(),
                            fmt_size(c.size),
                            c.path.display()
                        );
                    }
                }
                Err(e) => {
                    failed += 1;
                    if echo {
                        eprintln!(
                            "{} {} - {}",
                            "✗".red(),
                            c.path.display(),
                            e.to_string().dimmed()
                        );
                    }
                }
            }
        }
    }

    if echo {
        let prefix = if dry_run { "[DRY RUN] Would free" } else { "≈ Freed" };
        println!("{} {}", prefix, fmt_size(freed));
    }

    // Log to sweep log (only if not dry run)
    if !dry_run && freed > 0 {
        log_sweep(freed);
    }

    CleanResult {
        freed,
        deleted,
        failed,
    }
}
