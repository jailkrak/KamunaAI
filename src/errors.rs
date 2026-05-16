use thiserror::Error;
use std::io;

/// Main application error type
#[derive(Error, Debug)]
pub enum CyberScoutError {
    // ========== I/O & File Errors ==========
    #[error("File operation failed: {0}")]
    IoError(#[from] io::Error),

    #[error("Failed to read wordlist '{0}': {1}")]
    WordlistReadError(String, String),

    #[error("Invalid wordlist format: {0}")]
    WordlistFormatError(String),

    // ========== Network & HTTP Errors ==========
    #[error("HTTP request failed: {0}")]
    HttpRequestError(#[from] reqwest::Error),

    #[error("Invalid URL: {0}")]
    InvalidUrl(String),

    #[error("DNS resolution failed for '{0}': {1}")]
    DnsResolutionError(String, String),

    #[error("Connection timeout after {0} seconds")]
    ConnectionTimeout(u64),

    #[error("Request retry exhausted after {0} attempts")]
    RetryExhausted(usize),

    #[error("Proxy configuration error: {0}")]
    ProxyError(String),

    // ========== Configuration ==========
    #[error("Configuration error: {0}")]
    ConfigError(String),

    #[error("Invalid configuration value for '{0}': {1}")]
    InvalidConfigValue(String, String),

    #[error("Failed to parse config file: {0}")]
    ConfigParseError(#[from] serde_yaml::Error),

    // ========== Scanner Logic ==========
    #[error("Scan target is invalid or empty")]
    InvalidTarget,

    #[error("Scan mode not specified or recognized")]
    UnknownScanMode,

    #[error("Concurrent limit must be > 0, got {0}")]
    InvalidConcurrency(usize),

    #[error("Rate limit must be >= 0, got {0}")]
    InvalidRateLimit(i32),

    // ========== Output ==========
    #[error("Failed to write output file '{0}': {1}")]
    OutputWriteError(String, String),

    #[error("Unsupported output format: '{0}'")]
    UnsupportedOutputFormat(String),

    #[error("JSON serialization failed: {0}")]
    JsonSerializeError(#[from] serde_json::Error),

    // ========== Utility ==========
    #[error("Header parse error: {0}")]
    HeaderParseError(String),

    #[error("Invalid status code: {0}")]
    InvalidStatusCode(u16),

    #[error("Operation cancelled")]
    Cancelled,

    // ========== Generic ==========
    #[error("Unexpected error: {0}")]
    Unknown(String),

    #[error("Multiple errors occurred: {0:?}")]
    MultipleErrors(Vec<CyberScoutError>),
}

/// Result type alias
pub type Result<T> = std::result::Result<T, CyberScoutError>;


// =====================================================
// SAFE BRIDGE ONLY (fixes anyhow::Error for ? operator)
// =====================================================
impl From<anyhow::Error> for CyberScoutError {
    fn from(err: anyhow::Error) -> Self {
        CyberScoutError::Unknown(err.to_string())
    }
}


// =====================================================
// CORE METHODS (UNCHANGED LOGIC)
// =====================================================
impl CyberScoutError {

    /// Check retryable errors
    pub fn is_retryable(&self) -> bool {
        matches!(
            self,
            CyberScoutError::HttpRequestError(e)
            if e.is_timeout() || e.is_connect() || e.is_request()
        )
    }

    /// User friendly message
    pub fn user_message(&self) -> String {
        match self {
            CyberScoutError::WordlistReadError(path, _) =>
                format!("Could not read wordlist: {}", path),

            CyberScoutError::DnsResolutionError(domain, _) =>
                format!("Failed to resolve: {}", domain),

            CyberScoutError::ConnectionTimeout(secs) =>
                format!("Connection timed out after {}s", secs),

            CyberScoutError::RetryExhausted(attempts) =>
                format!("Gave up after {} attempts", attempts),

            CyberScoutError::InvalidTarget =>
                "Please provide a valid target".to_string(),

            CyberScoutError::ProxyError(_) =>
                "Proxy configuration error".to_string(),

            other => other.to_string(),
        }
    }

    /// Exit codes
    pub fn exit_code(&self) -> i32 {
        match self {
            CyberScoutError::Cancelled => 130,

            CyberScoutError::InvalidTarget
            | CyberScoutError::InvalidUrl(_)
            | CyberScoutError::WordlistReadError(_, _)
            | CyberScoutError::WordlistFormatError(_)
            | CyberScoutError::HeaderParseError(_)
            | CyberScoutError::InvalidStatusCode(_)
            | CyberScoutError::InvalidConcurrency(_)
            | CyberScoutError::InvalidRateLimit(_)
            | CyberScoutError::UnknownScanMode => 2,

            CyberScoutError::ConfigError(_)
            | CyberScoutError::InvalidConfigValue(_, _)
            | CyberScoutError::ConfigParseError(_) => 3,

            CyberScoutError::HttpRequestError(_)
            | CyberScoutError::DnsResolutionError(_, _)
            | CyberScoutError::ConnectionTimeout(_)
            | CyberScoutError::ProxyError(_) => 4,

            CyberScoutError::RetryExhausted(_) => 5,

            CyberScoutError::OutputWriteError(_, _)
            | CyberScoutError::UnsupportedOutputFormat(_)
            | CyberScoutError::JsonSerializeError(_) => 6,

            _ => 1,
        }
    }

    /// Optional logging helper (safe, no external trait conflict)
    pub fn log(&self) {
        use tracing::{error, warn, debug};

        match self {
            CyberScoutError::ConfigError(_)
            | CyberScoutError::ConfigParseError(_)
            | CyberScoutError::InvalidTarget
            | CyberScoutError::UnknownScanMode => {
                error!(error = ?self, "Critical error");
            }

            CyberScoutError::DnsResolutionError(_, _) => {
                debug!(error = ?self, "DNS resolution failed");
            }

            CyberScoutError::RetryExhausted(_)
            | CyberScoutError::HttpRequestError(_) => {
                warn!(error = ?self, "Request failed");
            }

            CyberScoutError::OutputWriteError(_, _)
            | CyberScoutError::JsonSerializeError(_) => {
                error!(error = ?self, "Output error");
            }

            _ => {
                warn!(error = ?self, "Unexpected error");
            }
        }
    }
}