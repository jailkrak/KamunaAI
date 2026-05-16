use clap::{Parser, ValueEnum};
use std::path::PathBuf;

#[derive(ValueEnum, Clone, Debug)]
pub enum ScanMode {
    Subdomain,
    Directory,
    Both,
}

#[derive(Parser, Debug)]
#[command(
    name = "cyber-scout",
    version,
    about = "🔍 High-performance cybersecurity reconnaissance tool",
    long_about = None,
    after_help = "Examples:
  cyber-scout -u example.com -w subdomains.txt
  cyber-scout --dir https://target.com -w folders.txt --threads 100
  cyber-scout -u example.com -w subs.txt -o results.json --proxy socks5://127.0.0.1:9050"
)]
pub struct CliArgs {
    /// Target domain for subdomain enumeration
    #[arg(short = 'u', long, required_unless_present = "dir")]
    pub domain: Option<String>,

    /// Target URL for directory brute-force
    #[arg(long, required_unless_present = "domain")]
    pub dir: Option<String>,

    /// Path to wordlist file
    #[arg(short = 'w', long, required = true)]
    pub wordlist: PathBuf,

    /// Output file path (auto-detect format: .txt or .json)
    #[arg(short = 'o', long)]
    pub output: Option<PathBuf>,

    /// Configuration file path
    #[arg(short = 'c', long, default_value = "config/default.yaml")]
    pub config: PathBuf,

    /// Number of concurrent threads
    #[arg(short = 't', long, default_value = "50")]
    pub concurrency: usize,

    /// Request timeout in seconds
    #[arg(long, default_value = "10")]
    pub timeout: u64,

    /// Maximum retry attempts per request
    #[arg(long, default_value = "3")]
    pub retries: u8,

    /// Rate limit: requests per second (0 = unlimited)
    #[arg(long, default_value = "0")]
    pub rate_limit: u32,

    /// Proxy URL (e.g., socks5://127.0.0.1:9050)
    #[arg(long)]
    pub proxy: Option<String>,

    /// Custom HTTP headers (format: "Header: Value")
    #[arg(long = "header", short = 'H', action = clap::ArgAction::Append)]
    pub headers: Vec<String>,

    /// Rotate User-Agent from predefined list
    #[arg(long)]
    pub rotate_ua: bool,

    /// Follow redirects
    #[arg(long, default_value = "true")]
    pub follow_redirects: bool,

    /// Filter status codes to display (comma-separated)
    #[arg(long, value_delimiter = ',', default_values = ["200", "301", "302", "403"])]
    pub filter_status: Vec<u16>,

    /// Suppress colored output
    #[arg(long)]
    pub no_color: bool,

    /// Enable verbose logging
    #[arg(short = 'v', long, action = clap::ArgAction::Count)]
    pub verbose: u8,

    /// Scan mode (auto-detected if not specified)
    #[arg(long, value_enum)]
    pub mode: Option<ScanMode>,

    /// Save raw HTTP responses (debug mode)
    #[arg(long, hide = true)]
    pub debug: bool,
}