use anyhow::{Result, Context};
use serde::{Deserialize, Serialize};
use std::{
    collections::HashMap,
    fs,
    path::{Path, PathBuf},
    time::Duration,
};
use tracing::debug;

/// Main application configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// HTTP client settings
    #[serde(default)]
    pub http: HttpClientConfig,
    
    /// DNS resolver settings
    #[serde(default)]
    pub dns: DnsConfig,
    
    /// Scanner behavior settings
    #[serde(default)]
    pub scanner: ScannerConfig,
    
    /// Output settings
    #[serde(default)]
    pub output: OutputConfig,
    
    /// Custom headers to include in all requests
    #[serde(default)]
    pub custom_headers: HashMap<String, String>,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            http: HttpClientConfig::default(),
            dns: DnsConfig::default(),
            scanner: ScannerConfig::default(),
            output: OutputConfig::default(),
            custom_headers: HashMap::new(),
        }
    }
}

impl Config {
    /// Load configuration from YAML file with fallback to defaults
    pub fn load(path: &Path) -> Result<Self> {
        debug!("Loading configuration from: {:?}", path);
        
        if !path.exists() {
            debug!("Config file not found, using defaults");
            return Ok(Self::default());
        }

        let content = fs::read_to_string(path)
            .with_context(|| format!("Failed to read config file: {:?}", path))?;

        let mut config: Config = serde_yaml::from_str(&content)
            .with_context(|| format!("Failed to parse config file: {:?}", path))?;

        // Merge custom_headers from top-level into http config for convenience
        if !config.custom_headers.is_empty() {
            for (key, value) in config.custom_headers.drain() {
                config.http.custom_headers.entry(key).or_insert(value);
            }
        }

        debug!("Configuration loaded successfully");
        Ok(config)
    }

    /// Merge CLI arguments into config (CLI takes precedence)
    pub fn merge_cli_args(&mut self, args: &crate::args::CliArgs) {
        // HTTP settings
        if args.timeout > 0 {
            self.http.timeout = args.timeout;
        }
        if args.retries > 0 {
            self.http.max_retries = args.retries as usize;
        }
        if args.follow_redirects {
            self.http.follow_redirects = true;
        }
        if args.rotate_ua {
            self.http.rotate_user_agent = true;
        }
        if let Some(ref proxy) = args.proxy {
            self.http.proxy = Some(proxy.clone());
        }
        
        // Add CLI headers
        for header in &args.headers {
            if let Some((key, value)) = header.split_once(':') {
                self.http.custom_headers.insert(
                    key.trim().to_string(),
                    value.trim().to_string(),
                );
            }
        }

        // Scanner settings
        if !args.filter_status.is_empty() {
            self.scanner.filter_status_codes = args.filter_status.clone();
        }
        if args.rate_limit > 0 {
            self.scanner.rate_limit_per_second = Some(args.rate_limit);
        }

        // DNS settings
        if let Some(ref dns_servers) = args.config.parent().and_then(|_p| {
            // Could add CLI DNS args here if needed
            None::<Vec<String>>
        }) {
            self.dns.name_servers = dns_servers.clone();
        }
    }
}

/// HTTP Client specific configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HttpClientConfig {
    /// Request timeout in seconds
    #[serde(default = "default_timeout")]
    pub timeout: u64,
    
    /// Connection timeout in seconds
    #[serde(default = "default_connect_timeout")]
    pub connect_timeout: u64,
    
    /// Maximum retry attempts for failed requests
    #[serde(default = "default_max_retries")]
    pub max_retries: usize,
    
    /// Retry backoff multiplier (exponential backoff)
    #[serde(default = "default_retry_backoff")]
    pub retry_backoff_ms: u64,
    
    /// Follow HTTP redirects automatically
    #[serde(default = "default_true")]
    pub follow_redirects: bool,
    
    /// Accept invalid SSL certificates (DANGEROUS - for testing only)
    #[serde(default)]
    pub allow_invalid_certs: bool,
    
    /// Rotate User-Agent header from predefined list
    #[serde(default)]
    pub rotate_user_agent: bool,
    
    /// Proxy URL (e.g., "socks5://127.0.0.1:9050")
    #[serde(default)]
    pub proxy: Option<String>,
    
    /// Custom HTTP headers
    #[serde(default)]
    pub custom_headers: HashMap<String, String>,
    
    /// Enable HTTP/2
    #[serde(default = "default_true")]
    pub http2: bool,
    
    /// Enable compression (gzip/brotli)
    #[serde(default = "default_true")]
    pub compression: bool,
}

impl Default for HttpClientConfig {
    fn default() -> Self {
        Self {
            timeout: default_timeout(),
            connect_timeout: default_connect_timeout(),
            max_retries: default_max_retries(),
            retry_backoff_ms: default_retry_backoff(),
            follow_redirects: default_true(),
            allow_invalid_certs: false,
            rotate_user_agent: false,
            proxy: None,
            custom_headers: HashMap::new(),
            http2: default_true(),
            compression: default_true(),
        }
    }
}

impl HttpClientConfig {
    pub fn timeout_duration(&self) -> Duration {
        Duration::from_secs(self.timeout)
    }

    pub fn connect_timeout_duration(&self) -> Duration {
        Duration::from_secs(self.connect_timeout)
    }

    pub fn retry_backoff(&self) -> Duration {
        Duration::from_millis(self.retry_backoff_ms)
    }
}

/// DNS Resolver configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DnsConfig {
    /// Custom DNS servers to use (empty = system default)
    #[serde(default)]
    pub name_servers: Vec<String>,
    
    /// DNS query timeout in seconds
    #[serde(default = "default_dns_timeout")]
    pub timeout: u64,
    
    /// Enable DNS caching
    #[serde(default = "default_true")]
    pub cache_enabled: bool,
    
    /// Cache TTL in seconds (if caching enabled)
    #[serde(default = "default_dns_cache_ttl")]
    pub cache_ttl: u64,
    
    /// Perform both A and AAAA record lookups
    #[serde(default = "default_true")]
    pub resolve_ipv6: bool,
}

impl Default for DnsConfig {
    fn default() -> Self {
        Self {
            name_servers: Vec::new(),
            timeout: default_dns_timeout(),
            cache_enabled: default_true(),
            cache_ttl: default_dns_cache_ttl(),
            resolve_ipv6: default_true(),
        }
    }
}

/// Scanner behavior configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScannerConfig {
    /// Status codes to include in results (empty = all)
    #[serde(default)]
    pub filter_status_codes: Vec<u16>,
    
    /// Status codes to exclude from results
    #[serde(default)]
    pub exclude_status_codes: Vec<u16>,
    
    /// Minimum content length to consider a result valid (0 = no filter)
    #[serde(default)]
    pub min_content_length: Option<u64>,
    
    /// Maximum content length to include (0 = no limit)
    #[serde(default)]
    pub max_content_length: Option<u64>,
    
    /// Rate limit: requests per second (None = unlimited)
    #[serde(default)]
    pub rate_limit_per_second: Option<u32>,
    
    /// Enable automatic HTTP → HTTPS fallback
    #[serde(default = "default_true")]
    pub https_fallback: bool,
    
    /// Extract page titles from HTML responses
    #[serde(default)]
    pub extract_titles: bool,
    
    /// Detect common technologies (WAF, frameworks, etc.)
    #[serde(default)]
    pub tech_detection: bool,
}

impl Default for ScannerConfig {
    fn default() -> Self {
        Self {
            filter_status_codes: vec![200, 301, 302, 403, 404],
            exclude_status_codes: vec![],
            min_content_length: None,
            max_content_length: None,
            rate_limit_per_second: None,
            https_fallback: default_true(),
            extract_titles: false,
            tech_detection: false,
        }
    }
}

impl ScannerConfig {
    pub fn should_include_status(&self, code: u16) -> bool {
        // Exclude list takes precedence
        if !self.exclude_status_codes.is_empty() 
            && self.exclude_status_codes.contains(&code) {
            return false;
        }
        
        // If filter list is empty, include everything not excluded
        if self.filter_status_codes.is_empty() {
            return true;
        }
        
        self.filter_status_codes.contains(&code)
    }

    pub fn should_include_content_length(&self, length: u64) -> bool {
        if let Some(min) = self.min_content_length {
            if length < min { return false; }
        }
        if let Some(max) = self.max_content_length {
            if max > 0 && length > max { return false; }
        }
        true
    }
}

/// Output configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputConfig {
    /// Enable colored terminal output
    #[serde(default = "default_true")]
    pub colored: bool,
    
    /// Show progress bar during scanning
    #[serde(default = "default_true")]
    pub show_progress: bool,
    
    /// Verbose output level (0 = quiet, 1 = normal, 2 = debug, 3 = trace)
    #[serde(default)]
    pub verbosity: u8,
    
    /// Save raw HTTP responses to file (debug mode)
    #[serde(default)]
    pub save_raw_responses: bool,
    
    /// Output directory for logs and exports
    #[serde(default)]
    pub output_dir: Option<PathBuf>,
}

impl Default for OutputConfig {
    fn default() -> Self {
        Self {
            colored: default_true(),
            show_progress: default_true(),
            verbosity: 0,
            save_raw_responses: false,
            output_dir: None,
        }
    }
}

// ============ Default Value Functions ============

fn default_timeout() -> u64 { 10 }
fn default_connect_timeout() -> u64 { 5 }
fn default_max_retries() -> usize { 3 }
fn default_retry_backoff() -> u64 { 500 }
fn default_dns_timeout() -> u64 { 5 }
fn default_dns_cache_ttl() -> u64 { 300 }
fn default_true() -> bool { true }

// ============ Unit Tests ============

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::NamedTempFile;
    use std::io::Write;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.http.timeout, 10);
        assert!(config.http.follow_redirects);
        assert!(config.scanner.https_fallback);
    }

    #[test]
    fn test_load_valid_yaml() -> Result<()> {
        let mut tmp = NamedTempFile::new()?;
        writeln!(tmp, r#"
http:
  timeout: 30
  max_retries: 5
scanner:
  filter_status_codes: [200, 403]
"#)?;

        let config = Config::load(tmp.path())?;
        assert_eq!(config.http.timeout, 30);
        assert_eq!(config.http.max_retries, 5);
        assert_eq!(config.scanner.filter_status_codes, vec![200, 403]);
        
        Ok(())
    }

    #[test]
    fn test_status_filter_logic() {
        let mut scanner = ScannerConfig::default();
        
        // Default: includes 200, 301, 302, 403, 404
        assert!(scanner.should_include_status(200));
        assert!(scanner.should_include_status(404));
        assert!(!scanner.should_include_status(500)); // Not in default list
        
        // Custom filter
        scanner.filter_status_codes = vec![200];
        assert!(scanner.should_include_status(200));
        assert!(!scanner.should_include_status(404));
        
        // Exclude takes precedence
        scanner.filter_status_codes = vec![200, 404];
        scanner.exclude_status_codes = vec![404];
        assert!(scanner.should_include_status(200));
        assert!(!scanner.should_include_status(404)); // Excluded
    }

    #[test]
    fn test_content_length_filter() {
        let mut scanner = ScannerConfig::default();
        
        assert!(scanner.should_include_content_length(1000));
        
        scanner.min_content_length = Some(500);
        assert!(!scanner.should_include_content_length(100));
        assert!(scanner.should_include_content_length(1000));
        
        scanner.max_content_length = Some(2000);
        assert!(scanner.should_include_content_length(1000));
        assert!(!scanner.should_include_content_length(5000));
    }
}