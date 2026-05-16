//! Unit/Integration Tests for Subdomain Scanning Logic
//! 
//! Focuses on the `scanner::subdomain` module behavior.

use cyber_scout::config::{Config, HttpClientConfig, DnsConfig, ScannerConfig};
use cyber_scout::scanner::subdomain::scan_single_subdomain;
use cyber_scout::scanner::http_client::AsyncHttpClient;
use cyber_scout::scanner::dns_resolver::DnsResolver;
use cyber_scout::errors::CyberScoutError;

#[tokio::test]
async fn test_scan_valid_subdomain() {
    let config = Config {
        http: HttpClientConfig::default(),
        dns: DnsConfig::default(),
        scanner: ScannerConfig::default(),
        ..Default::default()
    };
    
    let http_client = AsyncHttpClient::new(&config.http).unwrap();
    let dns_resolver = DnsResolver::new(&config.dns);
    
    // www.google.com is a reliable subdomain
    let result = scan_single_subdomain(
        "www.google.com", 
        &http_client, 
        &dns_resolver, 
        &config
    ).await;
    
    assert!(result.is_ok());
    let res = result.unwrap();
    assert_eq!(res.status_code, 200);
    assert!(res.resolved_ip.is_some());
}

#[tokio::test]
async fn test_scan_invalid_subdomain_dns_fail() {
    let config = Config {
        http: HttpClientConfig::default(),
        dns: DnsConfig::default(),
        scanner: ScannerConfig::default(),
        ..Default::default()
    };
    
    let http_client = AsyncHttpClient::new(&config.http).unwrap();
    let dns_resolver = DnsResolver::new(&config.dns);
    
    // Random non-existent subdomain
    let result = scan_single_subdomain(
        "this-subdomain-does-not-exist-xyz-123.google.com", 
        &http_client, 
        &dns_resolver, 
        &config
    ).await;
    
    // Should fail at DNS resolution
    assert!(result.is_err());
    
    if let Err(CyberScoutError::DnsResolutionError(_, _)) = result {
        // Expected
    } else {
        panic!("Expected DnsResolutionError");
    }
}

#[tokio::test]
async fn test_scan_subdomain_https_fallback() {
    let config = Config {
        http: HttpClientConfig::default(),
        dns: DnsConfig::default(),
        scanner: ScannerConfig {
            https_fallback: true,
            ..Default::default()
        },
        ..Default::default()
    };
    
    let http_client = AsyncHttpClient::new(&config.http).unwrap();
    let dns_resolver = DnsResolver::new(&config.dns);
    
    // Test a domain that supports HTTPS
    let result = scan_single_subdomain(
        "www.github.com", 
        &http_client, 
        &dns_resolver, 
        &config
    ).await;
    
    assert!(result.is_ok());
    let res = result.unwrap();
    assert!(res.final_url.starts_with("https://"));
}