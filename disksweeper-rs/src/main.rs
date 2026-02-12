mod browsers;
mod cleaner;
mod output;
mod rules;
mod scanner;

use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::collections::HashSet;
use std::path::PathBuf;

use rules::{find_config, load_rules, Severity};

#[derive(Parser)]
#[command(name = "dswp")]
#[command(author, version, about = "Fast disk cleanup CLI for Windows")]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,

    /// Path to custom rules YAML config
    #[arg(short, long, global = true)]
    config: Option<PathBuf>,

    /// Output as JSON
    #[arg(long, global = true)]
    json: bool,

    /// Suppress progress output
    #[arg(short, long, global = true)]
    quiet: bool,

    /// Control color output
    #[arg(long, global = true, default_value = "auto")]
    color: ColorChoice,
}

#[derive(Clone, Copy, PartialEq, Eq, clap::ValueEnum)]
enum ColorChoice {
    Auto,
    Always,
    Never,
}

#[derive(Subcommand)]
enum Commands {
    /// Scan and report candidates (dry-run, default)
    Report {
        /// Severities to include (comma-separated: safe,moderate,aggressive)
        #[arg(short, long, default_value = "safe,moderate,aggressive")]
        severity: String,
    },

    /// Delete safe + moderate tier items
    Clean {
        /// Severities to include (comma-separated)
        #[arg(short, long, default_value = "safe,moderate")]
        severity: String,

        /// Show what would be deleted without actually deleting
        #[arg(long)]
        dry_run: bool,
    },

    /// Delete ALL severity tiers (including aggressive)
    Deep {
        /// Show what would be deleted without actually deleting
        #[arg(long)]
        dry_run: bool,
    },

    /// List configured cleanup rules
    Rules,
}

fn parse_severities(s: &str) -> HashSet<Severity> {
    s.split(',')
        .filter_map(|part| part.trim().parse().ok())
        .collect()
}

fn setup_color(choice: ColorChoice) {
    match choice {
        ColorChoice::Auto => {
            // colored crate auto-detects by default
        }
        ColorChoice::Always => {
            colored::control::set_override(true);
        }
        ColorChoice::Never => {
            colored::control::set_override(false);
        }
    }
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    setup_color(cli.color);

    // Find config file
    let config_path = cli
        .config
        .or_else(find_config)
        .context("Could not find config file. Use --config to specify path or ensure data/default_rules.yaml exists.")?;

    // Load rules
    let rules = load_rules(&config_path)?;

    // Handle commands
    match cli.command.unwrap_or(Commands::Report {
        severity: "safe,moderate,aggressive".to_string(),
    }) {
        Commands::Report { severity } => {
            let include = parse_severities(&severity);
            let candidates = scanner::collect(&rules, &include);

            if cli.json {
                output::print_report_json(&candidates, "report");
            } else if !cli.quiet {
                output::print_report(&candidates, "report");
            }
        }

        Commands::Clean { severity, dry_run } => {
            let include = parse_severities(&severity);
            let candidates = scanner::collect(&rules, &include);

            if cli.json {
                let result = cleaner::clean(&candidates, false, dry_run);
                output::print_clean_json(&candidates, &result, "clean", dry_run);
            } else {
                let echo = !cli.quiet;
                if echo && !dry_run {
                    println!("\nCleaning selected candidates…");
                }
                cleaner::clean(&candidates, echo, dry_run);
            }
        }

        Commands::Deep { dry_run } => {
            let include: HashSet<Severity> =
                [Severity::Safe, Severity::Moderate, Severity::Aggressive]
                    .into_iter()
                    .collect();
            let candidates = scanner::collect(&rules, &include);

            if cli.json {
                let result = cleaner::clean(&candidates, false, dry_run);
                output::print_clean_json(&candidates, &result, "deep", dry_run);
            } else {
                let echo = !cli.quiet;
                if echo && !dry_run {
                    println!("\nDeep cleaning ALL candidates…");
                }
                cleaner::clean(&candidates, echo, dry_run);
            }
        }

        Commands::Rules => {
            if cli.json {
                output::print_rules_json(&rules);
            } else {
                output::print_rules(&rules);
            }
        }
    }

    Ok(())
}
