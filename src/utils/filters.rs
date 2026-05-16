//! Result Filtering & Deduplication
//! 
//! Provides utilities to filter scan results based on status codes, 
//! content length, and duplicate detection.

use std::collections::HashSet;
use sha2::{Sha256, Digest};
use crate::models::result::ScanResult;
use crate::config::ScannerConfig;

/// Check if a result should be included based on scanner config
pub fn should_include_result(result: &ScanResult, config: &ScannerConfig) -> bool {
    // 1. Status Code Filter
    if !config.should_include_status(result.status_code) {
        return false;
    }

    // 2. Content Length Filter
    if let Some(len) = result.content_length {
        if !config.should_include_content_length(len) {
            return false;
        }
    }

    true
}

/// Generate a unique hash for a result to detect duplicates
pub fn generate_result_hash(result: &ScanResult) -> String {
    let mut hasher = Sha256::new();
    hasher.update(result.target.as_bytes());
    hasher.update(result.final_url.as_bytes());
    hasher.update(result.status_code.to_string().as_bytes());
    
    // Include content length if available to distinguish same URL different content
    if let Some(len) = result.content_length {
        hasher.update(len.to_string().as_bytes());
    }

    format!("{:x}", hasher.finalize())
}

/// Filter a list of results to remove duplicates
pub fn deduplicate_results(results: Vec<ScanResult>) -> Vec<ScanResult> {
    let mut seen = HashSet::new();
    let mut unique = Vec::new();

    for result in results {
        let hash = generate_result_hash(&result);
        if seen.insert(hash) {
            unique.push(result);
        }
    }

    unique
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::result::{models::status::StatusCategory, ScanType};
    use chrono::Utc;

    fn mock_result(target: &str, code: u16) -> ScanResult {
        ScanResult {
            id: "id".into(),
            target: target.into(),
            resolved_ip: None,
            final_url: format!("https://{}", target),
            status_code: code,
            status_category: StatusCategory::from(code),
            content_length: Some(100),
            response_time_ms: 10,
            headers: None,
            redirect_chain: vec![],
            discovered_at: Utc::now(),
            scan_type: ScanType::Subdomain,
            title: None,
        }
    }

    #[test]
    fn test_deduplication() {
        let r1 = mock_result("a.com", 200);
        let r2 = mock_result("a.com", 200); // Duplicate
        let r3 = mock_result("b.com", 200); // Unique
        
        let results = vec![r1, r2, r3];
        let unique = deduplicate_results(results);
        
        assert_eq!(unique.len(), 2);
    }

    #[test]
    fn test_status_filter() {
        let mut config = ScannerConfig::default();
        config.filter_status_codes = vec![200];
        
        let r200 = mock_result("a.com", 200);
        let r404 = mock_result("b.com", 404);
        
        assert!(should_include_result(&r200, &config));
        assert!(!should_include_result(&r404, &config));
    }
}