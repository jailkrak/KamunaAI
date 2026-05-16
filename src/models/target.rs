//! Target Parsing and Validation
//! 
//! Provides robust parsing for domains and URLs to ensure safe scanning inputs.

use url::Url;
use crate::errors::{CyberScoutError, Result};

/// Represents a validated scan target
#[derive(Debug, Clone)]
pub struct Target {
    /// Original input string
    pub raw: String,
    /// Parsed URL (if applicable)
    pub url: Option<Url>,
    /// Hostname extracted from target
    pub host: String,
    /// Scheme (http/https)
    pub scheme: String,
}

impl Target {
    /// Parse a target string into a structured Target object
    pub fn parse(input: &str) -> Result<Self> {
        let input = input.trim();
        if input.is_empty() {
            return Err(CyberScoutError::InvalidTarget);
        }

        // Try to parse as URL first
        if let Ok(url) = Url::parse(input) {
            let host = url.host_str()
                .ok_or_else(|| CyberScoutError::InvalidUrl(input.to_string()))?
                .to_string();
            
            let scheme = url.scheme().to_string();

            return Ok(Self {
                raw: input.to_string(),
                url: Some(url),
                host,
                scheme,
            });
        }

        // If not a valid URL, treat as hostname (for subdomain enumeration)
        // Validate basic hostname characters
        if !Self::is_valid_hostname(input) {
            return Err(CyberScoutError::InvalidUrl(input.to_string()));
        }

        Ok(Self {
            raw: input.to_string(),
            url: None,
            host: input.to_string(),
            scheme: "https".to_string(), // Default assumption
        })
    }

    /// Check if string looks like a valid hostname
    fn is_valid_hostname(host: &str) -> bool {
        // Basic RFC 1123 check: alphanumeric, hyphens, dots
        // Must not start or end with hyphen
        // Must not have consecutive dots
        if host.is_empty() || host.len() > 253 {
            return false;
        }
        
        let parts: Vec<&str> = host.split('.').collect();
        for part in parts {
            if part.is_empty() || part.starts_with('-') || part.ends_with('-') {
                return false;
            }
            if !part.chars().all(|c| c.is_alphanumeric() || c == '-') {
                return false;
            }
        }
        
        true
    }

    /// Construct a full URL from this target
    pub fn to_url(&self, path: Option<&str>) -> String {
        let base = if let Some(ref url) = self.url {
            url.to_string()
        } else {
            format!("{}://{}", self.scheme, self.host)
        };

        if let Some(p) = path {
            // Ensure proper slash joining
            if base.ends_with('/') && p.starts_with('/') {
                format!("{}{}", base, &p[1..])
            } else if !base.ends_with('/') && !p.starts_with('/') {
                format!("{}/{}", base, p)
            } else {
                format!("{}{}", base, p)
            }
        } else {
            base
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_url() {
        let target = Target::parse("https://example.com/path").unwrap();
        assert_eq!(target.host, "example.com");
        assert_eq!(target.scheme, "https");
        assert!(target.url.is_some());
    }

    #[test]
    fn test_parse_hostname() {
        let target = Target::parse("sub.example.com").unwrap();
        assert_eq!(target.host, "sub.example.com");
        assert_eq!(target.scheme, "https");
        assert!(target.url.is_none());
    }

    #[test]
    fn test_invalid_hostname() {
        assert!(Target::parse("").is_err());
        assert!(Target::parse("-invalid.com").is_err());
        assert!(Target::parse("inv alid.com").is_err());
    }

    #[test]
    fn test_to_url_construction() {
        let target = Target::parse("example.com").unwrap();
        assert_eq!(target.to_url(None), "https://example.com");
        assert_eq!(target.to_url(Some("/login")), "https://example.com/login");
        
        let target2 = Target::parse("https://example.com/base/").unwrap();
        assert_eq!(target2.to_url(Some("path")), "https://example.com/base/path");
    }
}