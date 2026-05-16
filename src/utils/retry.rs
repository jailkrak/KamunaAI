//! Exponential Backoff Retry Logic
//! 
//! Wraps async operations with retry capabilities based on config settings.

use crate::errors::CyberScoutError;
use std::future::Future;
use std::time::Duration;
use tracing::warn;

/// Execute an async operation with exponential backoff retry
pub async fn with_retry<F, Fut, T>(
    mut operation: F,
    max_retries: usize,
    base_delay: Duration,
) -> Result<T, CyberScoutError>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, CyberScoutError>>,
{
    let mut attempts = 0;

    loop {
        match operation().await {
            Ok(value) => return Ok(value),
            Err(e) => {
                attempts += 1;
                if attempts > max_retries {
                    return Err(CyberScoutError::RetryExhausted(max_retries));
                }

                if e.is_retryable() {
                    let delay = base_delay * (2_u32.pow((attempts - 1) as u32));
                    warn!("Attempt {} failed: {}. Retrying in {:?}...", attempts, e, delay);
                    tokio::time::sleep(delay).await;
                } else {
                    // Non-retryable error, fail immediately
                    return Err(e);
                }
            }
        }
    }
}

/// Helper to create a retry closure for HTTP requests
pub async fn retry_http_request<F, Fut, T>(
    operation: F,
    max_retries: usize,
    base_delay_ms: u64,
) -> Result<T, CyberScoutError>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, CyberScoutError>>,
{
    with_retry(operation, max_retries, Duration::from_millis(base_delay_ms)).await
}