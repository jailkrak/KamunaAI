//! CyberScout - High-Performance Cybersecurity Reconnaissance Tool
//! Main entry point

#![allow(dead_code)]
#![allow(unused_imports)]
#![allow(unused_variables)]

use clap::Parser;
use tracing::debug;
use anyhow::{Result, Context};
use std::time::Instant;

// Internal Modules
mod args;
mod config;
mod errors;
mod models;
mod output;
mod scanner;
mod utils;

use args::CliArgs;
use config::Config;
use scanner::core::ReconScanner;
use output::{TerminalPrinter, save_results};
use utils::logger::init_logging;

#[tokio::main]
async fn main() -> Result<()> {
    // 1. Parse CLI Arguments
    let args = CliArgs::parse();

    // 2. Initialize Logging (silent unless verbose)
    init_logging(args.verbose)?;
    debug!("CLI Arguments parsed: {:?}", args);

    // 3. Load Configuration
    let mut config = Config::load(&args.config)
        .context("Failed to load configuration file")?;

    // 4. Merge CLI overrides
    config.merge_cli_args(&args);
    debug!("Final Configuration loaded");

    // 5. Output handler (clean user output)
    let printer = TerminalPrinter::new(!config.output.colored);
    printer.banner();

    // 6. Validate inputs (no logic change)
    if args.wordlist.exists() {
        debug!("Wordlist found: {:?}", args.wordlist);
    } else {
        printer.error(
            "Wordlist file not found",
            &args.wordlist.display().to_string()
        );
        return Err(anyhow::anyhow!("Wordlist file missing"));
    }

    // 7. Init scanner
    let start_time = Instant::now();
    let scanner = ReconScanner::new(config.clone(), args.concurrency)
        .context("Failed to initialize scanner")?;

    // 8. Execute scan
    let results = if let Some(domain) = &args.domain {
        printer.info(&format!(
            "Starting Subdomain Enumeration for: {}",
            domain
        ));
        scanner.scan_subdomains(domain, &args.wordlist).await?
    } else if let Some(url) = &args.dir {
        printer.info(&format!(
            "Starting Directory Brute-Force for: {}",
            url
        ));
        scanner.scan_directories(url, &args.wordlist).await?
    } else {
        printer.error(
            "No target specified",
            "Use -u for domain or --dir for URL"
        );
        return Err(anyhow::anyhow!("No target specified"));
    };

    // 9. Timing
    let duration = start_time.elapsed();
    printer.success(&format!(
        "Scan completed in {:.2}s",
        duration.as_secs_f64()
    ));

    // 10. Handle results (clean UX)
    if results.is_empty() {
        printer.warning("No results found matching your filters.");
    } else {
        printer.summary(&results);

        // Export if needed
        if let Some(output_path) = &args.output {
            match save_results(&results, output_path) {
                Ok(_) => printer.success(&format!(
                    "Results saved to: {}",
                    output_path.display()
                )),
                Err(e) => {
                    printer.error("Failed to save results", &e.to_string());

                    // Keep original error logging behavior (DO NOT REMOVE)
                    e.log();
                }
            }
        }
    }

    Ok(())
}