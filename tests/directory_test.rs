//! Unit/Integration Tests for Directory Scanning Logic
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
            filter_status_codes: vec![200],
            ..Default::default()
        },
        ..Default::default()
    };

    let http_client = AsyncHttpClient::new(&config.http).unwrap();

    let result = scan_single_directory(
        "https://httpbin.org/status/404",
        &http_client,
        &config
    ).await;

    //  Expect error (filtered by status code rule)
    assert!(result.is_err());

    match result {
        Err(CyberScoutError::Unknown(msg)) => {
            // flexible check (do not depend on exact "Filtered" wording)
            assert!(
                msg.to_lowercase().contains("filter")
                || msg.to_lowercase().contains("status")
                || msg.to_lowercase().contains("blocked")
            );
        }
        Err(_) => panic!("Expected Unknown filter-related error"),
        Ok(_) => panic!("Expected error but got Ok"),
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

    let result = scan_single_directory(
        "https://httpbin.org/redirect-to?url=https://example.com",
        &http_client,
        &config
    ).await;

    assert!(result.is_ok());

    let res = result.unwrap();

    // Should follow redirect
    assert_eq!(res.status_code, 200);
    assert!(res.final_url.contains("example.com"));
}