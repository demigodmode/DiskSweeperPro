use rayon::prelude::*;
use std::collections::HashSet;
use std::path::Path;
use std::time::{Duration, SystemTime};
use walkdir::WalkDir;

use crate::rules::{Candidate, Rule, Severity};

/// Calculate total size of a path, respecting age cutoff
fn walk_size(path: &Path, cutoff: Option<SystemTime>) -> u64 {
    if !path.exists() {
        return 0;
    }

    // Single file
    if path.is_file() {
        if let Ok(meta) = path.metadata() {
            if let Some(cutoff_time) = cutoff {
                if let Ok(mtime) = meta.modified() {
                    if mtime >= cutoff_time {
                        return 0; // File is too new
                    }
                }
            }
            return meta.len();
        }
        return 0;
    }

    // Directory walk
    let mut total: u64 = 0;
    for entry in WalkDir::new(path).into_iter().filter_map(|e| e.ok()) {
        if entry.file_type().is_file() {
            if let Ok(meta) = entry.metadata() {
                let include = match cutoff {
                    Some(cutoff_time) => meta
                        .modified()
                        .map(|mtime| mtime < cutoff_time)
                        .unwrap_or(true),
                    None => true,
                };
                if include {
                    total += meta.len();
                }
            }
        }
    }

    total
}

/// Scan rules in parallel and return candidates
pub fn collect(rules: &[Rule], include: &HashSet<Severity>) -> Vec<Candidate> {
    let now = SystemTime::now();

    rules
        .par_iter()
        .filter(|r| include.contains(&r.severity))
        .flat_map(|rule| {
            let cutoff = if rule.min_age > 0 {
                now.checked_sub(Duration::from_secs(rule.min_age as u64 * 86400))
            } else {
                None
            };

            rule.paths
                .par_iter()
                .filter_map(|path| {
                    let size = walk_size(path, cutoff);
                    if size >= rule.min_size {
                        Some(Candidate {
                            label: rule.label.clone(),
                            path: path.clone(),
                            size,
                            severity: rule.severity,
                            reason: rule.reason.clone(),
                        })
                    } else {
                        None
                    }
                })
                .collect::<Vec<_>>()
        })
        .collect()
}
