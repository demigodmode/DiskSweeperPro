use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

use crate::browsers::{chrome_caches, edge_caches};

// ── Constants ──────────────────────────────────────────────────────────────

pub const MB: u64 = 1024 * 1024;
pub const GB: u64 = 1024 * 1024 * 1024;

// ── Severity ───────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Severity {
    Safe,
    Moderate,
    Aggressive,
}

impl Severity {
    pub fn order(&self) -> u8 {
        match self {
            Severity::Safe => 0,
            Severity::Moderate => 1,
            Severity::Aggressive => 2,
        }
    }
}

impl std::fmt::Display for Severity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Severity::Safe => write!(f, "safe"),
            Severity::Moderate => write!(f, "moderate"),
            Severity::Aggressive => write!(f, "aggressive"),
        }
    }
}

impl std::str::FromStr for Severity {
    type Err = anyhow::Error;

    fn from_str(s: &str) -> Result<Self> {
        match s.to_lowercase().as_str() {
            "safe" => Ok(Severity::Safe),
            "moderate" => Ok(Severity::Moderate),
            "aggressive" => Ok(Severity::Aggressive),
            _ => anyhow::bail!("Invalid severity: {}", s),
        }
    }
}

// ── Rule ───────────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct Rule {
    pub label: String,
    pub paths: Vec<PathBuf>,
    pub min_size: u64,
    pub min_age: u32, // days
    pub severity: Severity,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct Candidate {
    pub label: String,
    pub path: PathBuf,
    pub size: u64,
    pub severity: Severity,
    pub reason: String,
}

// ── YAML parsing ───────────────────────────────────────────────────────────

#[derive(Debug, Deserialize)]
struct RawRule {
    label: String,
    path: String,
    #[serde(default)]
    min_size: u64,
    #[serde(default)]
    min_age: u32,
    #[serde(default = "default_severity")]
    severity: Severity,
    #[serde(default)]
    reason: String,
}

fn default_severity() -> Severity {
    Severity::Safe
}

fn get_local_appdata() -> PathBuf {
    dirs::data_local_dir().unwrap_or_else(|| {
        let home = dirs::home_dir().unwrap_or_default();
        home.join("AppData").join("Local")
    })
}

fn get_system_root() -> PathBuf {
    std::env::var("SYSTEMROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("C:\\Windows"))
}

fn expand_path(path_str: &str) -> PathBuf {
    let local = get_local_appdata();
    let system_root = get_system_root();

    let expanded = path_str
        .replace("{LOCAL}", local.to_str().unwrap_or(""))
        .replace("{SYSTEM_ROOT}", system_root.to_str().unwrap_or(""));

    // Handle ~ for home directory
    if expanded.starts_with('~') {
        if let Some(home) = dirs::home_dir() {
            return home.join(&expanded[2..]);
        }
    }

    PathBuf::from(expanded)
}

pub fn load_rules(config_path: &PathBuf) -> Result<Vec<Rule>> {
    let content = std::fs::read_to_string(config_path)
        .with_context(|| format!("Failed to read config: {}", config_path.display()))?;

    let raw_rules: Vec<RawRule> =
        serde_yaml::from_str(&content).context("Failed to parse YAML config")?;

    let mut rules = Vec::new();

    for raw in raw_rules {
        let paths = match raw.path.as_str() {
            "edge_caches" => edge_caches(),
            "chrome_caches" => chrome_caches(),
            _ => {
                let expanded = expand_path(&raw.path);
                // Handle glob patterns (e.g., PyCharm*)
                if raw.path.contains('*') {
                    if let Some(parent) = expanded.parent() {
                        if let Some(pattern) = expanded.file_name() {
                            let pattern_str = pattern.to_string_lossy();
                            let prefix = pattern_str.trim_end_matches('*');
                            if parent.exists() {
                                std::fs::read_dir(parent)
                                    .ok()
                                    .map(|entries| {
                                        entries
                                            .filter_map(|e| e.ok())
                                            .filter(|e| {
                                                e.file_name()
                                                    .to_string_lossy()
                                                    .starts_with(prefix)
                                            })
                                            .map(|e| e.path())
                                            .collect()
                                    })
                                    .unwrap_or_else(Vec::new)
                            } else {
                                vec![]
                            }
                        } else {
                            vec![expanded]
                        }
                    } else {
                        vec![expanded]
                    }
                } else {
                    vec![expanded]
                }
            }
        };

        rules.push(Rule {
            label: raw.label,
            paths,
            min_size: raw.min_size,
            min_age: raw.min_age,
            severity: raw.severity,
            reason: raw.reason,
        });
    }

    Ok(rules)
}

pub fn find_config() -> Option<PathBuf> {
    // Try relative to executable first
    if let Ok(exe) = std::env::current_exe() {
        if let Some(exe_dir) = exe.parent() {
            // Check ../data/default_rules.yaml (when running from target/release)
            let config = exe_dir
                .parent()
                .and_then(|p| p.parent())
                .map(|p| p.join("data").join("default_rules.yaml"));
            if let Some(ref path) = config {
                if path.exists() {
                    return config;
                }
            }
        }
    }

    // Try current directory
    let cwd_config = PathBuf::from("data/default_rules.yaml");
    if cwd_config.exists() {
        return Some(cwd_config);
    }

    // Try parent directory (when running from disksweeper-rs/)
    let parent_config = PathBuf::from("../data/default_rules.yaml");
    if parent_config.exists() {
        return Some(parent_config);
    }

    None
}
