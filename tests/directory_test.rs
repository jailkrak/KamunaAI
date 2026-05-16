//! Unit/Integration Tests for Directory Scanning Logic
//! 
//! Focuses on the `scanner::directory` module behavior.

use cyber_scout::config::{Config, HttpClientConfig, ScannerConfig};
use cyber_scout::scanner::directory::scan_single_directory;
use cyber_scout::scanner::http_client::AsyncHttpClient;
use cyber_scout::errors::CyberScoutError;

#[tokio::test]
async fn test_scan_existing_directory() {
    let config = Config {
        http: HttpClientConfig::default(),
        scanner: ScannerConfig::default(),
        ..Default::default()
    };
    
    let http_client = AsyncHttpClient::new(&config.http).unwrap();
    
    // httpbin.org/status/200 is a reliable endpoint
    let result = scan_single_directory(
        "https://httpbin.org/status/200", 
        &http_client, 
        &config
    ).await;
    
    assert!(result.is_ok());
    let res = result.unwrap();
    assert_eq!(res.status_code, 200);
    assert_eq!(res.target, "https://httpbin.org/status/200");
}

#[tokio::test]
async fn test_scan_non_existent_directory() {
    let config = Config {
        http: HttpClientConfig::default(),
        scanner: ScannerConfig {
            filter_status_codes: vec![200], // Only allow 200
            ..Default::default()
        },
        ..Default::default()
    };
    
    let http_client = AsyncHttpClient::new(&config.http).unwrap();
    
    // This path likely doesn't exist
    let result = scan_single_directory(
        "https://httpbin.org/status/404", 
        &http_client, 
        &config
    ).await;
    
    // Since we filter for 200 only, this should return an Error (Filtered)
    assert!(result.is_err());
    
    if let Err(CyberScoutError::Unknown(msg)) = result {
        assert!(msg.contains("Filtered"));
    } else {
        panic!("Expected Filtered Error");
    }
}

#[tokio::test]
async fn test_scan_redirect() {
    let config = Config {
        http: HttpClientConfig {
            follow_redirects: true,
            ..Default::default()
        },
        scanner: ScannerConfig {
            filter_status_codes: vec![200, 301, 302],
            ..Default::default()
        },
        ..Default::default()
    };
    
    let http_client = AsyncHttpClient::new(&config.http).unwrap();
    
    // httpbin redirects to google
    let result = scan_single_directory(
        "https://httpbin.org/redirect-to?url=https://example.com", 
        &http_client, 
        &config
    ).await;
    
    assert!(result.is_ok());
    let res = result.unwrap();
    // Should follow redirect to 200
    assert_eq!(res.status_code, 200); 
    assert!(res.final_url.contains("example.com"));
}