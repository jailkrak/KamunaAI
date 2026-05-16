//! Directory/Path brute-force logic
//! 
//! Probes URL paths, handles redirects, status codes, and content filters.
//! Thread-safe for concurrent execution via core scanner.

use crate::config::Config;
use crate::errors::{CyberScoutError, Result};
use crate::models::result::ScanResult;
use crate::scanner::http_client::AsyncHttpClient;
use std::time::Instant;
use tracing::debug;

/// Scan a single directory/path target
/// 
/// Workflow:
/// 1. Normalize URL (ensure scheme)
/// 2. Send request with HTTPS fallback
/// 3. Apply status & content-length filters
/// 4. Return structured result
pub async fn scan_single_directory(
    target_url: &str,
    http_client: &AsyncHttpClient,
    config: &Config,
) -> Result<ScanResult> {
    debug!("Scanning directory: {}", target_url);
    let scan_start = Instant::now();

    // 1. Normalize URL
    let url = if target_url.starts_with("http://") || target_url.starts_with("https://") {
        target_url.to_string()
    } else {
        format!("https://{}", target_url)
    };

    // 2. HTTP Request
    let (final_url, response) = if config.scanner.https_fallback {
        http_client.get_with_fallback(&url).await?
    } else {
        let resp = http_client.get(&url).await?;
        (url, resp)
    };

    let total_elapsed = scan_start.elapsed().as_millis() as u64;

    // 3. Build Result
    let mut result = ScanResult::directory(
        target_url,
        response,
        final_url,
    );
    result.response_time_ms = total_elapsed;

    // 4. Status Code Filter
    if !config.scanner.should_include_status(result.status_code) {
        return Err(CyberScoutError::Unknown(
            format!("Filtered by status: {}", result.status_code)
        ));
    }

    // 5. Content Length Filter
    if let Some(len) = result.content_length {
        if !config.scanner.should_include_content_length(len) {
            return Err(CyberScoutError::Unknown(
                "Filtered by content length".into()
            ));
        }
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{Config, HttpClientConfig, ScannerConfig};

    #[tokio::test]
    #[ignore] // Requires network
    async fn test_directory_scan_integration() {
        let config = Config {
            http: HttpClientConfig::default(),
            scanner: ScannerConfig::default(),
            ..Default::default()
        };
        
        let http_client = AsyncHttpClient::new(&config.http).unwrap();
        
        // Test against known path
        let result = scan_single_directory("https://httpbin.org/status/200", &http_client, &config).await;
        assert!(result.is_ok());
        assert_eq!(result.unwrap().status_code, 200);
    }
}