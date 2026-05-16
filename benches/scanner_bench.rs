//! Performance Benchmarks for CyberScout
//!
//! Measures:
//! 1. DNS Resolution throughput (concurrent)
//! 2. HTTP Request latency (async concurrency)
//! 3. Result Serialization speed (JSON/TXT)
//! 4. Wordlist Parsing speed
//!
//! Run with: cargo bench

use criterion::{black_box, criterion_group, criterion_main, Criterion, BatchSize};
use tokio::runtime::Runtime;
use std::sync::Arc;
use std::time::Duration;

// Internal crates
use cyber_scout::config::{Config, HttpClientConfig, DnsConfig, ScannerConfig};
use cyber_scout::scanner::{DnsResolver, AsyncHttpClient};
use cyber_scout::models::result::{ScanResult, StatusCategory, ScanType};
use cyber_scout::output::exporter::save_results;
use chrono::Utc;

// ============================================================================
// 1. DNS Resolution Benchmark
// ============================================================================

fn bench_dns_resolution(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    
    // Setup Config
    let config = Config {
        dns: DnsConfig {
            timeout: 5,
            cache_enabled: false, // Disable cache to test raw resolution speed
            ..Default::default()
        },
        ..Default::default()
    };
    
    let resolver = DnsResolver::new(&config.dns);
    
    // Targets: Mix of popular domains to ensure high availability
    let targets = vec![
        "google.com", "github.com", "amazon.com", "microsoft.com", 
        "cloudflare.com", "apple.com", "netflix.com", "twitter.com",
        "facebook.com", "linkedin.com"
    ];

    let mut group = c.benchmark_group("dns_resolution");
    group.measurement_time(Duration::from_secs(10));

    group.bench_function("resolve_10_concurrent", |b| {
        b.to_async(&rt).iter_batched(
            || targets.clone(),
            |batch| {
                let resolver = resolver.clone();
                async move {
                    // Resolve all concurrently
                    let futs = batch.iter().map(|t| resolver.resolve(t));
                    futures::future::join_all(futs).await;
                }
            },
            BatchSize::SmallInput
        )
    });

    group.finish();
}

// ============================================================================
// 2. HTTP Client Benchmark
// ============================================================================

fn bench_http_client(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();

    let config = Config {
        http: HttpClientConfig {
            timeout: 10,
            follow_redirects: true,
            compression: true,
            ..Default::default()
        },
        ..Default::default()
    };

    let client = Arc::new(AsyncHttpClient::new(&config.http).unwrap());
    
    // Stable endpoints for testing
    let urls = vec![
        "https://httpbin.org/get",
        "https://httpbin.org/status/200",
        "https://httpbin.org/delay/1", // Test timeout handling
    ];

    let mut group = c.benchmark_group("http_client");
    group.measurement_time(Duration::from_secs(15)); // Longer for network calls

    group.bench_function("get_single_request", |b| {
        b.to_async(&rt).iter(|| {
            let client = client.clone();
            async move {
                let _resp = client.get("https://httpbin.org/get").await.unwrap();
            }
        })
    });

    group.bench_function("get_with_fallback", |b| {
        b.to_async(&rt).iter(|| {
            let client = client.clone();
            async move {
                // Tests the HTTPS -> HTTP fallback logic overhead
                let _resp = client.get_with_fallback("https://httpbin.org/get").await.unwrap();
            }
        })
    });

    group.finish();
}

// ============================================================================
// 3. Serialization Benchmark (Export)
// ============================================================================

fn bench_serialization(c: &mut Criterion) {
    // Generate mock results
    let mock_results: Vec<ScanResult> = (0..1000)
        .map(|i| ScanResult {
            id: format!("uuid-{}", i),
            target: format!("subdomain-{}.example.com", i),
            resolved_ip: Some(format!("192.168.1.{}", i % 255)),
            final_url: format!("https://subdomain-{}.example.com/login", i),
            status_code: if i % 5 == 0 { 404 } else { 200 },
            status_category: if i % 5 == 0 { StatusCategory::ClientError } else { StatusCategory::Success },
            content_length: Some(1024 + i as u64),
            response_time_ms: 50 + (i % 100) as u64,
            headers: None,
            redirect_chain: vec![],
            discovered_at: Utc::now(),
            scan_type: ScanType::Subdomain,
            title: Some("Test Page".to_string()),
        })
        .collect();

    let mut group = c.benchmark_group("serialization");

    // JSON Export
    group.bench_function("export_json_1000_results", |b| {
        b.iter(|| {
            let temp_path = std::env::temp_dir().join("bench_export.json");
            save_results(black_box(&mock_results), &temp_path).unwrap();
            // Cleanup
            let _ = std::fs::remove_file(&temp_path);
        })
    });

    // TXT Export
    group.bench_function("export_txt_1000_results", |b| {
        b.iter(|| {
            let temp_path = std::env::temp_dir().join("bench_export.txt");
            save_results(black_box(&mock_results), &temp_path).unwrap();
            // Cleanup
            let _ = std::fs::remove_file(&temp_path);
        })
    });

    group.finish();
}

// ============================================================================
// 4. Wordlist Parsing Benchmark
// ============================================================================

fn bench_wordlist_parsing(c: &mut Criterion) {
    // Create a large temporary wordlist
    let temp_dir = std::env::temp_dir();
    let wordlist_path = temp_dir.join("bench_wordlist.txt");
    
    let lines: String = (0..50_000)
        .map(|i| format!("entry-number-{}\n", i))
        .collect();
    std::fs::write(&wordlist_path, &lines).unwrap();

    let mut group = c.benchmark_group("wordlist_parsing");

    group.bench_function("parse_50k_lines", |b| {
        b.iter(|| {
            // Replicate the logic in scanner/core.rs::load_wordlist
            let content = std::fs::read_to_string(&wordlist_path).unwrap();
            let entries: Vec<String> = content
                .lines()
                .map(str::trim)
                .filter(|l| !l.is_empty() && !l.starts_with('#'))
                .map(String::from)
                .collect();
            
            black_box(entries.len())
        })
    });

    group.finish();
    
    // Cleanup
    let _ = std::fs::remove_file(&wordlist_path);
}

// ============================================================================
// Criterion Configuration
// ============================================================================

criterion_group!(
    name = benches;
    config = Criterion::default()
        .sample_size(100)
        .warm_up_time(Duration::from_secs(2));
    targets = bench_dns_resolution, bench_http_client, bench_serialization, bench_wordlist_parsing
);

criterion_main!(benches);