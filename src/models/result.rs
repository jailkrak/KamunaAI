//! Scan Result Structure
//! 
//! The canonical representation of a single scan finding.
//! Used for JSON/TXT export, terminal printing, and filtering.

use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

use crate::models::status::StatusCategory;

/// Type of scan performed
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub enum ScanType {
    Subdomain,
    Directory,
}

/// Key-Value pair for HTTP Headers
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeaderKV {
    pub name: String,
    pub value: String,
}

/// Represents a single successful or failed scan attempt
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanResult {
    /// Unique identifier for this result entry
    pub id: String,
    
    /// The original target input (e.g., "admin.example.com" or "/login")
    pub target: String,
    
    /// Resolved IP address (only for subdomain scans)
    pub resolved_ip: Option<String>,
    
    /// The final URL after any redirects
    pub final_url: String,
    
    /// HTTP Status Code (e.g., 200, 404, 301)
    pub status_code: u16,
    
    /// Categorized status (Success, Redirect, ClientError, etc.)
    pub status_category: StatusCategory,
    
    /// Content-Length header value, if present
    pub content_length: Option<u64>,
    
    /// Time taken for the request in milliseconds
    pub response_time_ms: u64,
    
    /// Response headers (optional, can be large)
    pub headers: Option<Vec<HeaderKV>>,
    
    /// Chain of URLs visited during redirection
    pub redirect_chain: Vec<String>,
    
    /// Timestamp when the result was discovered
    pub discovered_at: DateTime<Utc>,
    
    /// Type of scan that produced this result
    pub scan_type: ScanType,
    
    /// HTML <title> tag content, if extracted
    pub title: Option<String>,
}

impl ScanResult {
    /// Construct a new result from an HTTP response (Subdomain context)
    pub fn subdomain(
        target: &str,
        resolved_ip: Option<String>,
        response: reqwest::Response,
        final_url: String,
    ) -> Self {
        Self::build(
            target,
            resolved_ip,
            response,
            final_url,
            ScanType::Subdomain,
        )
    }

    /// Construct a new result from an HTTP response (Directory context)
    pub fn directory(
        target: &str,
        response: reqwest::Response,
        final_url: String,
    ) -> Self {
        Self::build(
            target,
            None,
            response,
            final_url,
            ScanType::Directory,
        )
    }

    /// Internal builder to reduce code duplication
    fn build(
        target: &str,
        resolved_ip: Option<String>,
        response: reqwest::Response,
        final_url: String,
        scan_type: ScanType,
    ) -> Self {
        let status = response.status().as_u16();

        // Extract headers
        let headers = response
            .headers()
            .iter()
            .map(|(k, v)| HeaderKV {
                name: k.as_str().to_string(),
                value: v.to_str().unwrap_or("<binary>").to_string(),
            })
            .collect::<Vec<_>>();

        // reqwest Response does not expose redirect history directly.
        // Keep compatibility by storing final URL as redirect chain.
        let redirect_chain = vec![final_url.clone()];

        Self {
            id: Uuid::new_v4().to_string(),
            target: target.to_string(),
            resolved_ip,
            final_url,
            status_code: status,
            status_category: StatusCategory::from(status),
            content_length: response.content_length(),
            response_time_ms: 0, // To be updated externally
            headers: if headers.is_empty() {
                None
            } else {
                Some(headers)
            },
            redirect_chain,
            discovered_at: Utc::now(),
            scan_type,
            title: None,
        }
    }

    /// Update response time after scan timing is measured
    pub fn set_response_time(&mut self, ms: u64) {
        self.response_time_ms = ms;
    }

    /// Set extracted HTML title
    pub fn set_title<T: Into<String>>(&mut self, title: T) {
        self.title = Some(title.into());
    }

    /// Add redirect URL into chain
    pub fn add_redirect<T: Into<String>>(&mut self, url: T) {
        self.redirect_chain.push(url.into());
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scan_result_serialization() {
        let result = ScanResult {
            id: "test-id".into(),
            target: "example.com".into(),
            resolved_ip: Some("93.184.216.34".into()),
            final_url: "https://example.com".into(),
            status_code: 200,
            status_category: StatusCategory::Success,
            content_length: Some(1234),
            response_time_ms: 50,
            headers: None,
            redirect_chain: vec![],
            discovered_at: Utc::now(),
            scan_type: ScanType::Subdomain,
            title: Some("Example Domain".into()),
        };

        let json = serde_json::to_string(&result).unwrap();

        assert!(json.contains("\"status_code\":200"));
        assert!(json.contains("\"scan_type\":\"Subdomain\""));
    }

    #[test]
    fn test_redirect_chain() {
        let mut result = ScanResult {
            id: "test".into(),
            target: "example.com".into(),
            resolved_ip: None,
            final_url: "https://example.com".into(),
            status_code: 301,
            status_category: StatusCategory::Redirect,
            content_length: None,
            response_time_ms: 0,
            headers: None,
            redirect_chain: vec![],
            discovered_at: Utc::now(),
            scan_type: ScanType::Directory,
            title: None,
        };

        result.add_redirect("http://example.com");
        result.add_redirect("https://example.com");

        assert_eq!(result.redirect_chain.len(), 2);
    }

    #[test]
    fn test_setters() {
        let mut result = ScanResult {
            id: "test".into(),
            target: "example.com".into(),
            resolved_ip: None,
            final_url: "https://example.com".into(),
            status_code: 200,
            status_category: StatusCategory::Success,
            content_length: None,
            response_time_ms: 0,
            headers: None,
            redirect_chain: vec![],
            discovered_at: Utc::now(),
            scan_type: ScanType::Directory,
            title: None,
        };

        result.set_response_time(150);
        result.set_title("Dashboard");

        assert_eq!(result.response_time_ms, 150);
        assert_eq!(result.title.unwrap(), "Dashboard");
    }
}