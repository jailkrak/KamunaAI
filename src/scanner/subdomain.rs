//! Subdomain enumeration logic
//! 
//! Combines DNS resolution + HTTP probing to validate active subdomains.
//! Designed for single-target execution; concurrency handled by core scanner.

use crate::config::Config;
use crate::errors::{CyberScoutError, Result};
use crate::models::result::ScanResult;
use crate::scanner::dns_resolver::DnsResolver;
use crate::scanner::http_client::AsyncHttpClient;
use std::time::Instant;
use tracing::debug;

/// Scan a single subdomain target
/// 
/// Workflow:
/// 1. Resolve DNS (with cache)
/// 2. Probe HTTPS first, fallback to HTTP if configured
/// 3. Capture response metrics & build ScanResult
pub async fn scan_single_subdomain(
    subdomain: &str,
    http_client: &AsyncHttpClient,
    dns_resolver: &DnsResolver,
    config: &Config,
) -> Result<ScanResult> {
    debug!("Scanning subdomain: {}", subdomain);
    let scan_start = Instant::now();

    // 1. DNS Resolution
    let ip = dns_resolver.resolve(subdomain).await?;
    if ip.is_none() {
        return Err(CyberScoutError::DnsResolutionError(
            subdomain.to_string(),
            "No A/AAAA records found".into(),
        ));
    }

    // 2. HTTP/HTTPS Probing
    let base_url = format!("https://{}", subdomain);
    let (final_url, response) = if config.scanner.https_fallback {
        http_client.get_with_fallback(&base_url).await?
    } else {
        let resp = http_client.get(&base_url).await?;
        (base_url, resp)
    };

    let total_elapsed = scan_start.elapsed().as_millis() as u64;

    // 3. Build Result Model
    let mut result = ScanResult::subdomain(
        subdomain,
        ip.map(|i| i.to_string()),
        response,
        final_url,
    );
    result.response_time_ms = total_elapsed;

    // 4. Apply Server-Side Filters (if configured)
    if !config.scanner.should_include_status(result.status_code) {
        return Err(CyberScoutError::Unknown(
            format!("Filtered by status: {}", result.status_code)
        ));
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{Config, DnsConfig, HttpClientConfig, ScannerConfig};

    #[tokio::test]
    #[ignore] // Requires network
    async fn test_subdomain_scan_integration() {
        let config = Config {
            dns: DnsConfig::default(),
            http: HttpClientConfig::default(),
            scanner: ScannerConfig::default(),
            ..Default::default()
        };
        
        let http_client = AsyncHttpClient::new(&config.http).unwrap();
        let dns_resolver = DnsResolver::new(&config.dns);
        
        // Test against a known subdomain
        let result = scan_single_subdomain("www.google.com", &http_client, &dns_resolver, &config).await;
        assert!(result.is_ok());
        let scan = result.unwrap();
        assert_eq!(scan.status_code, 200);
    }
}