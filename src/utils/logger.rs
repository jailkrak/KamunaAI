//! Logging initialization
//! 
//! Configures `tracing-subscriber` based on CLI verbosity levels.

use anyhow::Result;
use tracing_subscriber::{fmt, EnvFilter};

/// Initialize the global tracing subscriber
pub fn init_logging(verbosity: u8) -> Result<()> {
    let filter = match verbosity {
        0 => EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("cyber_scout=info")),
        1 => EnvFilter::new("cyber_scout=debug"),
        2 => EnvFilter::new("cyber_scout=trace"),
        _ => EnvFilter::new("trace"),
    };

    fmt::Subscriber::builder()
        .with_env_filter(filter)
        .with_target(false) // Hide target module path for cleaner CLI output
        .without_time()     // Hide timestamp for cleaner CLI output
        .with_writer(std::io::stderr) // Log to stderr so stdout remains clean for results
        .init();

    Ok(())
}