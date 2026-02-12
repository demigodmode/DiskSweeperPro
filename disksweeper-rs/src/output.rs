use colored::Colorize;
use serde::Serialize;

use crate::cleaner::CleanResult;
use crate::rules::{Candidate, Severity, GB, MB};

pub fn fmt_size(bytes: u64) -> String {
    if bytes >= GB {
        format!("{:.1} GB", bytes as f64 / GB as f64)
    } else if bytes >= MB {
        format!("{:.1} MB", bytes as f64 / MB as f64)
    } else {
        format!("{} B", bytes)
    }
}

fn severity_colored(severity: Severity) -> colored::ColoredString {
    match severity {
        Severity::Safe => "safe".green(),
        Severity::Moderate => "moderate".yellow(),
        Severity::Aggressive => "aggressive".red(),
    }
}

fn truncate(s: &str, max_len: usize) -> String {
    if s.len() <= max_len {
        s.to_string()
    } else {
        format!("{}…", &s[..max_len - 1])
    }
}

pub fn print_report(candidates: &[Candidate], mode: &str) {
    let total: u64 = candidates.iter().map(|c| c.size).sum();

    println!("Disk-cleanup review");
    println!(
        "Mode: {} | Candidates: {} | Potential space: {}",
        mode,
        candidates.len(),
        fmt_size(total)
    );
    println!("{}", "—".repeat(88));

    // Sort by severity order, then by size descending
    let mut sorted: Vec<_> = candidates.iter().collect();
    sorted.sort_by(|a, b| {
        let sev_cmp = a.severity.order().cmp(&b.severity.order());
        if sev_cmp == std::cmp::Ordering::Equal {
            b.size.cmp(&a.size)
        } else {
            sev_cmp
        }
    });

    for c in sorted {
        let reason = truncate(&c.reason, 48);
        println!(
            "{:>9}  {:<22} {:<10} {}",
            fmt_size(c.size),
            c.label,
            severity_colored(c.severity),
            reason.dimmed()
        );
        println!("{:>13}{}", "", c.path.display().to_string().dimmed());
    }

    println!("{}", "—".repeat(88));
}

// ── JSON output ────────────────────────────────────────────────────────────

#[derive(Serialize)]
pub struct JsonCandidate {
    pub label: String,
    pub path: String,
    pub size: u64,
    pub size_human: String,
    pub severity: String,
    pub reason: String,
}

#[derive(Serialize)]
pub struct JsonReport {
    pub mode: String,
    pub candidates: Vec<JsonCandidate>,
    pub total_size: u64,
    pub total_size_human: String,
}

#[derive(Serialize)]
pub struct JsonCleanResult {
    pub mode: String,
    pub dry_run: bool,
    pub candidates: Vec<JsonCandidate>,
    pub freed: u64,
    pub freed_human: String,
    pub deleted: usize,
    pub failed: usize,
}

impl From<&Candidate> for JsonCandidate {
    fn from(c: &Candidate) -> Self {
        JsonCandidate {
            label: c.label.clone(),
            path: c.path.display().to_string(),
            size: c.size,
            size_human: fmt_size(c.size),
            severity: c.severity.to_string(),
            reason: c.reason.clone(),
        }
    }
}

pub fn print_report_json(candidates: &[Candidate], mode: &str) {
    let total: u64 = candidates.iter().map(|c| c.size).sum();

    let report = JsonReport {
        mode: mode.to_string(),
        candidates: candidates.iter().map(JsonCandidate::from).collect(),
        total_size: total,
        total_size_human: fmt_size(total),
    };

    println!("{}", serde_json::to_string_pretty(&report).unwrap());
}

pub fn print_clean_json(candidates: &[Candidate], result: &CleanResult, mode: &str, dry_run: bool) {
    let output = JsonCleanResult {
        mode: mode.to_string(),
        dry_run,
        candidates: candidates.iter().map(JsonCandidate::from).collect(),
        freed: result.freed,
        freed_human: fmt_size(result.freed),
        deleted: result.deleted,
        failed: result.failed,
    };

    println!("{}", serde_json::to_string_pretty(&output).unwrap());
}

// ── Rules output ───────────────────────────────────────────────────────────

use crate::rules::Rule;

#[derive(Serialize)]
pub struct JsonRule {
    pub label: String,
    pub paths: Vec<String>,
    pub min_size: u64,
    pub min_size_human: String,
    pub min_age: u32,
    pub severity: String,
    pub reason: String,
}

pub fn print_rules(rules: &[Rule]) {
    println!("Configured cleanup rules:");
    println!("{}", "—".repeat(88));

    for rule in rules {
        println!(
            "{:<22} {:<10} min_size: {:>9}  min_age: {} days",
            rule.label,
            severity_colored(rule.severity),
            fmt_size(rule.min_size),
            rule.min_age
        );
        for path in &rule.paths {
            println!("  → {}", path.display().to_string().dimmed());
        }
        if !rule.reason.is_empty() {
            println!("    {}", rule.reason.dimmed());
        }
        println!();
    }
}

pub fn print_rules_json(rules: &[Rule]) {
    let json_rules: Vec<JsonRule> = rules
        .iter()
        .map(|r| JsonRule {
            label: r.label.clone(),
            paths: r.paths.iter().map(|p| p.display().to_string()).collect(),
            min_size: r.min_size,
            min_size_human: fmt_size(r.min_size),
            min_age: r.min_age,
            severity: r.severity.to_string(),
            reason: r.reason.clone(),
        })
        .collect();

    println!("{}", serde_json::to_string_pretty(&json_rules).unwrap());
}
