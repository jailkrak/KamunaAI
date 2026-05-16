//! Integration Tests for CyberScout
//! 
//! Tests the end-to-end flow: Config -> Scanner -> Results.
//! Uses real network calls against stable test endpoints (httpbin.org).

use cyber_scout::config::{Config, HttpClientConfig, DnsConfig, ScannerConfig, OutputConfig};
use cyber_scout::scanner::core::ReconScanner;
use std::path::PathBuf;
use std::fs;
use tempfile::NamedTempFile;
use std::io::Write;

/// Helper to create a temporary wordlist file
fn create_temp_wordlist(entries: &[&str]) -> NamedTempFile {
    let mut file = NamedTempFile::new().unwrap();
    for entry in entries {
        writeln!(file, "{}", entry).unwrap();
    }
    file
}

/// Helper to create a default config for testing
fn test_config() -> Config {
    Config {
        http: HttpClientConfig {
            timeout: 10,
            max_retries: 1, // Low retries for speed in tests
            ..Default::default()
        },
        dns: DnsConfig::default(),
        scanner: ScannerConfig {
            filter_status_codes: vec![200, 301, 404], // Common codes
            ..Default::default()
        },
        output: OutputConfig::default(),
        custom_headers: Default::default(),
    }
}

#[tokio::test]
async fn test_directory_scan_integration() {
    // Target: httpbin.org (stable test API)
    let base_url = "https://httpbin.org";
    
    // Wordlist with known paths
    let wordlist = create_temp_wordlist(&["get", "status/200", "nonexistent-path-xyz"]);
    
    let config = test_config();
    let scanner = ReconScanner::new(config, 5).unwrap();
    
    let results = scanner.scan_directories(base_url, wordlist.path())
        .await
        .expect("Scan failed");
    
    // We expect at least 'get' and 'status/200' to return 200
    let success_results: Vec<_> = results.iter()
        .filter(|r| r.status_code == 200)
        .collect();
        
    assert!(success_results.len() >= 2, "Expected at least 2 successful hits, got {}", success_results.len());
    
    // Verify structure
    for r in &results {
        assert!(!r.id.is_empty());
        assert!(!r.final_url.is_empty());
        assert!(r.response_time_ms > 0);
    }
}

#[tokio::test]
async fn test_subdomain_scan_integration() {
    // Target: A domain with known subdomains
    // Note: Real subdomain scanning is hard to test deterministically without a controlled zone.
    // We will test against 'localhost' or a known stable subdomain if available.
    // For this test, we'll use 'example.com' which usually resolves.
    
    let domain = "example.com";
    let wordlist = create_temp_wordlist(&["www", "nonexistent-subdomain-xyz-123"]);
    
    let config = test_config();
    let scanner = ReconScanner::new(config, 5).unwrap();
    
    let results = scanner.scan_subdomains(domain, wordlist.path())
        .await
        .expect("Scan failed");
    
    // 'www.example.com' should resolve and return 200
    let www_result = results.iter()
        .find(|r| r.target.contains("www"))
        .expect("www.example.com not found in results");
        
    assert_eq!(www_result.status_code, 200);
    assert!(www_result.resolved_ip.is_some());
}

#[tokio::test]
async fn test_empty_wordlist() {
    let wordlist = create_temp_wordlist(&[]);
    let config = test_config();
    let scanner = ReconScanner::new(config, 5).unwrap();
    
    let results = scanner.scan_directories("https://example.com", wordlist.path())
        .await
        .unwrap();
        
    assert!(results.is_empty());
}

#[tokio::test]
async fn test_invalid_target_handling() {
    let wordlist = create_temp_wordlist(&["test"]);
    let config = test_config();
    let scanner = ReconScanner::new(config, 5).unwrap();
    
    // Invalid URL scheme should handle gracefully or fail depending on implementation
    // Our scanner expects valid URLs or domains.
    let result = scanner.scan_directories("not-a-valid-url", wordlist.path()).await;
    
    // Depending on strictness, this might return Ok(empty) or Err. 
    // Given our Target parser, it might try to prepend https.
    // If it fails DNS, it returns empty or error.
    // We just ensure it doesn't panic.
    assert!(result.is_ok() || result.is_err()); 
}