//! Proxy Configuration Helper
//! 
//! Parses proxy strings and validates formats for reqwest.

use crate::errors::{CyberScoutError, Result};
use reqwest::Proxy;

/// Parse a proxy string into a reqwest Proxy object
pub fn parse_proxy(proxy_url: &str) -> Result<Proxy> {
    Proxy::all(proxy_url).map_err(|e| {
        CyberScoutError::ProxyError(format!("Invalid proxy URL '{}': {}", proxy_url, e))
    })
}

/// Validate proxy format without creating the object
pub fn is_valid_proxy_format(url: &str) -> bool {
    url.starts_with("http://") 
        || url.starts_with("https://") 
        || url.starts_with("socks5://")
        || url.starts_with("socks5h://")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_proxy_formats() {
        assert!(is_valid_proxy_format("http://127.0.0.1:8080"));
        assert!(is_valid_proxy_format("socks5://127.0.0.1:9050"));
        assert!(!is_valid_proxy_format("ftp://proxy"));
        assert!(!is_valid_proxy_format("invalid"));
    }

    #[test]
    fn test_parse_proxy_error() {
        let result = parse_proxy("not-a-url");
        assert!(result.is_err());
    }
}