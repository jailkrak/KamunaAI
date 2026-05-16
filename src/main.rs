//! CyberScout - High-Performance Cybersecurity Reconnaissance Tool
//!
//! Main entry point. Handles CLI parsing, configuration loading,
//! scanner initialization, and result export.

use clap::Parser;
use tracing::{info, error, debug};
use anyhow::{Result, Context};
use std::path::PathBuf;
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

    // 2. Initialize Logging (based on verbosity)
    init_logging(args.verbose)?;
    debug!("CLI Arguments parsed: {:?}", args);

    // 3. Load Configuration
    let mut config = Config::load(&args.config)
        .context("Failed to load configuration file")?;
    
    // 4. Merge CLI overrides into Config (CLI takes precedence)
    config.merge_cli_args(&args);
    debug!("Final Configuration loaded");

    // 5. Initialize Output Handler
    let printer = TerminalPrinter::new(!config.output.colored);
    printer.banner();

    // 6. Validate Inputs
    if args.wordlist.exists() {
        debug!("Wordlist found: {:?}", args.wordlist);
    } else {
        printer.error("Wordlist file not found", &args.wordlist.display().to_string());
        return Err(anyhow::anyhow!("Wordlist file missing"));
    }

    // 7. Initialize Scanner
    let start_time = Instant::now();
    let scanner = ReconScanner::new(config.clone(), args.concurrency)
        .context("Failed to initialize scanner")?;

    // 8. Execute Scan based on Mode
    let results = if let Some(domain) = &args.domain {
        printer.info(&format!("Starting Subdomain Enumeration for: {}", domain));
        scanner.scan_subdomains(domain, &args.wordlist).await?
    } else if let Some(url) = &args.dir {
        printer.info(&format!("Starting Directory Brute-Force for: {}", url));
        scanner.scan_directories(url, &args.wordlist).await?
    } else {
        // This case should be caught by Clap's required_unless_present, 
        // but kept as a safeguard.
        printer.error("No target specified", "Use -u for domain or --dir for URL");
        return Err(anyhow::anyhow!("No target specified"));
    };

    let duration = start_time.elapsed();
    printer.success(&format!("Scan completed in {:.2}s", duration.as_secs_f64()));

    // 9. Handle Results
    if results.is_empty() {
        printer.warning("No results found matching your filters.");
    } else {
        // Print summary to terminal
        printer.summary(&results);

        // Export to file if requested
        if let Some(output_path) = &args.output {
            match save_results(&results, output_path) {
                Ok(_) => printer.success(&format!("Results saved to: {}", output_path.display())),
                Err(e) => {
                    printer.error("Failed to save results", &e.to_string());
                    e.log(); // Log detailed error
                }
            }
        }
    }

    Ok(())
}