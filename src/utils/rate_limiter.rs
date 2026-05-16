//! Token Bucket Rate Limiter
//!
//! Implements a simple async token bucket algorithm to limit requests per second.
//! Thread-safe via Arc and Mutex.

use std::sync::Arc;
use tokio::sync::Mutex;
use std::time::{Duration, Instant};

pub struct RateLimiter {
    state: Arc<Mutex<RateLimiterState>>,
    interval: Duration,
}

struct RateLimiterState {
    last_request: Instant,
}

impl RateLimiter {
    /// Create a new rate limiter
    /// `requests_per_second`: Max requests allowed per second.
    pub fn new(requests_per_second: u32) -> Self {
        // Prevent division by zero
        let requests_per_second = requests_per_second.max(1);

        let interval = Duration::from_secs_f64(
            1.0 / requests_per_second as f64
        );

        Self {
            state: Arc::new(Mutex::new(RateLimiterState {
                last_request: Instant::now(),
            })),
            interval,
        }
    }

    /// Acquire a token.
    /// Blocks until the rate limit allows the next request.
    pub async fn acquire(&self) {

        // First lock scope
        {
            let state = self.state.lock().await;

            let now = Instant::now();
            let elapsed = now.duration_since(state.last_request);

            // Need to wait
            if elapsed < self.interval {
                let wait_time = self.interval - elapsed;

                // Explicitly release lock before sleeping
                drop(state);

                tokio::time::sleep(wait_time).await;
            }
        }

        // Re-lock after waiting
        let mut state = self.state.lock().await;
        state.last_request = Instant::now();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Instant;

    #[tokio::test]
    async fn test_rate_limiting() {

        // 10 requests/sec = 100ms interval
        let limiter = RateLimiter::new(10);

        let start = Instant::now();

        limiter.acquire().await;
        limiter.acquire().await;

        let elapsed = start.elapsed();

        // Should wait around 100ms
        assert!(elapsed >= Duration::from_millis(90));
    }

    #[tokio::test]
    async fn test_zero_requests_per_second() {

        // Should not panic/divide by zero
        let limiter = RateLimiter::new(0);

        limiter.acquire().await;
    }

    #[tokio::test]
    async fn test_multiple_requests() {

        let limiter = RateLimiter::new(5);

        let start = Instant::now();

        for _ in 0..3 {
            limiter.acquire().await;
        }

        let elapsed = start.elapsed();

        // ~400ms expected minimum
        assert!(elapsed >= Duration::from_millis(350));
    }
} 