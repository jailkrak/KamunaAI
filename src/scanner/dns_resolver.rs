//! High-performance async DNS resolver with TTL-based caching
//! 
//! Uses hickory-resolver (modern trust-dns fork) for fast, concurrent lookups.
//! Thread-safe via Arc and RwLock for use across Tokio tasks.

use crate::config::DnsConfig;
use crate::errors::{CyberScoutError, Result};

use hickory_resolver::config::{ResolverConfig, ResolverOpts};
use hickory_resolver::TokioAsyncResolver;

use std::collections::HashMap;
use std::net::IpAddr;
use std::sync::Arc;
use std::time::{Duration, Instant};

use tokio::sync::RwLock;

#[derive(Clone)]
pub struct DnsResolver {
    /// Async DNS resolver instance
    inner: Arc<TokioAsyncResolver>,

    /// In-memory cache: hostname -> (IP, timestamp)
    cache: Arc<RwLock<HashMap<String, (IpAddr, Instant)>>>,

    /// Cache entry lifetime
    ttl: Duration,
}

impl DnsResolver {
    /// Initialize DNS resolver from configuration
    pub fn new(config: &DnsConfig) -> Self {
        let mut opts = ResolverOpts::default();

        opts.timeout = Duration::from_secs(config.timeout);

        // Disable internal cache if we manage our own cache
        opts.cache_size = 0;

        // FIX:
        // TokioAsyncResolver::tokio() in hickory-resolver 0.24
        // no longer returns Result, so no .expect()
        let resolver = TokioAsyncResolver::tokio(
            ResolverConfig::default(),
            opts,
        );

        Self {
            inner: Arc::new(resolver),
            cache: Arc::new(RwLock::new(HashMap::new())),
            ttl: Duration::from_secs(config.cache_ttl),
        }
    }

    /// Resolve hostname to IPv4/IPv6 address
    ///
    /// Returns:
    /// - Ok(Some(IpAddr)) => resolved successfully
    /// - Ok(None) => no records / NXDOMAIN
    /// - Err(...) => actual resolver/network failure
    pub async fn resolve(&self, hostname: &str) -> Result<Option<IpAddr>> {
        // =========================================================
        // 1. Check cache first
        // =========================================================
        {
            let cache = self.cache.read().await;

            if let Some((ip, timestamp)) = cache.get(hostname) {
                if timestamp.elapsed() < self.ttl {
                    return Ok(Some(*ip));
                }
            }
        }

        // =========================================================
        // 2. Perform DNS lookup
        // =========================================================
        let lookup = self.inner.lookup_ip(hostname).await;

        match lookup {
            Ok(ips) => {
                if let Some(ip) = ips.iter().next() {
                    // Update cache
                    {
                        let mut cache = self.cache.write().await;

                        cache.insert(
                            hostname.to_string(),
                            (ip, Instant::now()),
                        );
                    }

                    Ok(Some(ip))
                } else {
                    // No A/AAAA records
                    Ok(None)
                }
            }

            Err(e) => {
                let err_msg = e.to_string();

                // Expected "not found" style cases
                if err_msg.contains("NXDOMAIN")
                    || err_msg.contains("no records found")
                    || err_msg.contains("SERVFAIL")
                {
                    Ok(None)
                } else {
                    Err(CyberScoutError::DnsResolutionError(
                        hostname.to_string(),
                        err_msg,
                    ))
                }
            }
        }
    }

    /// Clear entire cache
    pub async fn clear_cache(&self) {
        let mut cache = self.cache.write().await;
        cache.clear();
    }

    /// Get current cache size
    pub async fn cache_size(&self) -> usize {
        let cache = self.cache.read().await;
        cache.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_resolver_cache_hit() {
        let config = DnsConfig::default();

        let resolver = DnsResolver::new(&config);

        // First request populates cache
        let _ = resolver.resolve("localhost").await.unwrap();

        // Second request should be instant
        let start = Instant::now();

        let _ = resolver.resolve("localhost").await.unwrap();

        assert!(start.elapsed() < Duration::from_millis(5));
    }

    #[tokio::test]
    async fn test_cache_size() {
        let config = DnsConfig::default();

        let resolver = DnsResolver::new(&config);

        let _ = resolver.resolve("localhost").await;

        let size = resolver.cache_size().await;

        assert!(size >= 1);
    }

    #[tokio::test]
    async fn test_clear_cache() {
        let config = DnsConfig::default();

        let resolver = DnsResolver::new(&config);

        let _ = resolver.resolve("localhost").await;

        resolver.clear_cache().await;

        assert_eq!(resolver.cache_size().await, 0);
    }
}