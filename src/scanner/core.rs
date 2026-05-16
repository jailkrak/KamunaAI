//! Core scanning engine
//!
//! Orchestrates concurrent scanning, manages shared resources (DNS, HTTP clients),
//! handles progress tracking, deduplication, and result aggregation.

use std::collections::HashSet;
use std::path::Path;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::{Mutex, Semaphore};
use futures::stream::{self, StreamExt};
use indicatif::{ProgressBar, ProgressStyle};
use tracing::{debug, info};

use crate::config::Config;
use crate::errors::{CyberScoutError, Result};
use crate::models::result::ScanResult;
use crate::scanner::{DnsResolver, AsyncHttpClient, subdomain, directory};
use crate::utils::rate_limiter::RateLimiter; // Expected interface: new(rps), acquire().await

/// Internal task mode to route scanning logic
#[derive(Clone, Copy)]
enum TaskMode { Subdomain, Directory }

/// Main reconnaissance scanner orchestrator
pub struct ReconScanner {
    config: Arc<Config>,
    http_client: Arc<AsyncHttpClient>,
    dns_resolver: Arc<DnsResolver>,
    concurrency: usize,
    rate_limiter: Option<Arc<RateLimiter>>,
    seen_targets: Arc<Mutex<HashSet<String>>>,
}

impl ReconScanner {
    /// Initialize scanner with configuration and concurrency limits
    pub fn new(config: Config, concurrency: usize) -> Result<Self> {
        let concurrency = concurrency.clamp(1, 500);

        // Initialize shared async components
        let http_client = Arc::new(AsyncHttpClient::new(&config.http)?);
        let dns_resolver = Arc::new(DnsResolver::new(&config.dns));

        // Optional rate limiting
        let rate_limiter = config.scanner.rate_limit_per_second.map(|rps| {
            Arc::new(RateLimiter::new(rps))
        });

        Ok(Self {
            config: Arc::new(config),
            http_client,
            dns_resolver,
            concurrency,
            rate_limiter,
            seen_targets: Arc::new(Mutex::new(HashSet::new())),
        })
    }

    /// Scan subdomains for a given base domain
    pub async fn scan_subdomains(
        &self,
        domain: &str,
        wordlist_path: &Path,
    ) -> Result<Vec<ScanResult>> {
        let targets = Self::load_wordlist(wordlist_path)?
            .into_iter()
            .map(|entry| format!("{}.{}", entry, domain))
            .collect::<Vec<_>>();

        self.run_scan(targets, TaskMode::Subdomain).await
    }

    /// Scan directories/paths for a given base URL
    pub async fn scan_directories(
        &self,
        base_url: &str,
        wordlist_path: &Path,
    ) -> Result<Vec<ScanResult>> {
        let base = base_url.trim_end_matches('/');
        let targets = Self::load_wordlist(wordlist_path)?
            .into_iter()
            .map(|entry| format!("{}/{}", base, entry))
            .collect::<Vec<_>>();

        self.run_scan(targets, TaskMode::Directory).await
    }

    /// Core concurrent scanning loop
    async fn run_scan(&self, targets: Vec<String>, mode: TaskMode) -> Result<Vec<ScanResult>> {
        let total = targets.len();
        if total == 0 {
            return Ok(Vec::new());
        }

        let semaphore = Arc::new(Semaphore::new(self.concurrency));
        let pb = Self::create_progress_bar(total);
        let results: Arc<Mutex<Vec<ScanResult>>> = Arc::new(Mutex::new(Vec::with_capacity(total / 10)));
        let config = self.config.clone();

        // Process targets concurrently
        let tasks = stream::iter(targets)
            .map(|target| {
                let sem = semaphore.clone();
                let http = self.http_client.clone();
                let dns = self.dns_resolver.clone();
                let config = config.clone();
                let pb = pb.clone();
                let results = results.clone();
                let seen = self.seen_targets.clone();
                let limiter = self.rate_limiter.clone();

                async move {
                    // 1. Acquire concurrency permit
                    let _permit = sem.acquire().await.unwrap();

                    // 2. Apply rate limiting if configured
                    if let Some(limiter) = limiter {
                        limiter.acquire().await;
                    }

                    // 3. Deduplicate targets
                    let mut seen_guard = seen.lock().await;
                    if seen_guard.contains(&target) {
                        pb.inc(1);
                        return;
                    }
                    seen_guard.insert(target.clone());
                    drop(seen_guard);

                    // 4. Execute scan task
                    let scan_result = match mode {
                        TaskMode::Subdomain => {
                            subdomain::scan_single_subdomain(&target, &http, &dns, &config).await
                        }
                        TaskMode::Directory => {
                            directory::scan_single_directory(&target, &http, &config).await
                        }
                    };

                    // 5. Handle result
                    match scan_result {
                        Ok(res) => {
                            let mut res_guard = results.lock().await;
                            res_guard.push(res);
                        }
                        Err(e) => {
                            // Silently skip filtered results
                            let is_filtered = matches!(
                                &e,
                                CyberScoutError::Unknown(msg) if msg.starts_with("Filtered")
                            );
                            
                            if !is_filtered {
                                debug!("Skipped {}: {}", target, e);
                            }
                        }
                    }

                    // 6. Update progress
                    pb.inc(1);
                }
            })
            .buffer_unordered(self.concurrency);

        // Execute all tasks concurrently
        tasks.collect::<Vec<_>>().await;
        pb.finish_and_clear();

        // Extract final results
        let final_results = Arc::try_unwrap(results)
            .expect("Failed to unwrap results mutex")
            .into_inner();

        info!("Scan complete. Found {} valid targets.", final_results.len());
        Ok(final_results)
    }

    /// Parse wordlist file, ignoring comments & empty lines
    fn load_wordlist(path: &Path) -> Result<Vec<String>> {
        std::fs::read_to_string(path)
            .map(|content| {
                content
                    .lines()
                    .map(str::trim)
                    .filter(|l| !l.is_empty() && !l.starts_with('#'))
                    .map(String::from)
                    .collect()
            })
            .map_err(|e| CyberScoutError::WordlistReadError(
                path.display().to_string(),
                e.to_string(),
            ))
    }

    /// Create styled progress bar for CLI output
    fn create_progress_bar(total: usize) -> ProgressBar {
        let pb = ProgressBar::new(total as u64);
        pb.set_style(
            ProgressStyle::with_template(
                "{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta}) {msg}"
            )
            .unwrap()
            .progress_chars("#>-"),
        );
        pb.enable_steady_tick(Duration::from_millis(120));
        pb
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{HttpClientConfig, DnsConfig, ScannerConfig, OutputConfig};

    #[test]
    fn test_scanner_init() {
        let config = Config {
            http: HttpClientConfig::default(),
            dns: DnsConfig::default(),
            scanner: ScannerConfig::default(),
            output: OutputConfig::default(),
            custom_headers: Default::default(),
        };
        
        let scanner = ReconScanner::new(config, 50);
        assert!(scanner.is_ok());
        assert_eq!(scanner.unwrap().concurrency, 50);
    }

    #[test]
    fn test_wordlist_loader() {
        use std::io::Write;
        use tempfile::NamedTempFile;

        let mut tmp = NamedTempFile::new().unwrap();
        writeln!(tmp, "admin\n#comment\n\nlogin\n../test").unwrap();

        let entries = ReconScanner::load_wordlist(tmp.path()).unwrap();
        assert_eq!(entries, vec!["admin", "login", "../test"]);
    }
}