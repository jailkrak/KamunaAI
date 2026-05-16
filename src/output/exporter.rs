//! Result export logic
//! 
//! Supports saving scan results to JSON (structured) and TXT (human-readable) formats.
//! Automatically detects format based on file extension.

use std::fs::File;
use std::io::{self, Write};
use std::path::Path;
use chrono::Utc;
use serde_json;
use tracing::debug;

use crate::errors::{CyberScoutError, Result};
use crate::models::result::ScanResult;

/// Save scan results to a file. Format is auto-detected by extension (.json or .txt).
pub fn save_results(results: &[ScanResult], output_path: &Path) -> Result<()> {
    if results.is_empty() {
        debug!("No results to export");
        return Ok(());
    }

    let ext = output_path.extension()
        .and_then(|e| e.to_str())
        .unwrap_or("txt")
        .to_lowercase();

    match ext.as_str() {
        "json" => save_json(results, output_path),
        "txt" | "log" | "csv" => save_txt(results, output_path), // CSV treated as TXT for now
        _ => {
            debug!("Unknown extension '{}', defaulting to JSON", ext);
            save_json(results, &output_path.with_extension("json"))
        }
    }
}

/// Export results as pretty-printed JSON with metadata
fn save_json(results: &[ScanResult], path: &Path) -> Result<()> {
    debug!("Exporting {} results to JSON: {:?}", results.len(), path);

    let report = serde_json::json!({
        "metadata": {
            "tool": "cyber-scout",
            "version": env!("CARGO_PKG_VERSION"),
            "generated_at": Utc::now(),
            "total_results": results.len(),
            "status_summary": generate_status_summary(results)
        },
        "results": results
    });

    let json_string = serde_json::to_string_pretty(&report)
        .map_err(CyberScoutError::JsonSerializeError)?;

    std::fs::write(path, json_string)
        .map_err(|e| CyberScoutError::OutputWriteError(
            path.display().to_string(), 
            e.to_string()
        ))?;

    Ok(())
}

/// Export results as human-readable text log
fn save_txt(results: &[ScanResult], path: &Path) -> Result<()> {
    debug!("Exporting {} results to TXT: {:?}", results.len(), path);

    let mut file = File::create(path)
        .map_err(|e| CyberScoutError::OutputWriteError(
            path.display().to_string(), 
            e.to_string()
        ))?;

    // Header
    writeln!(file, "# CyberScout Scan Report")
        .map_err(io_error_to_scout)?;
    writeln!(file, "# Generated: {}", Utc::now())
        .map_err(io_error_to_scout)?;
    writeln!(file, "# Total Results: {}\n", results.len())
        .map_err(io_error_to_scout)?;

    // Column Headers
    writeln!(
        file, 
        "{:<6} {:<40} {:<50} {:<10} {:<8}", 
        "STATUS", 
        "TARGET", 
        "FINAL URL", 
        "SIZE(B)", 
        "TIME(ms)"
    )
    .map_err(io_error_to_scout)?;
    writeln!(file, "{}", "-".repeat(120))
        .map_err(io_error_to_scout)?;

    // Rows
    for r in results {
        let size = r.content_length.unwrap_or(0);
        let time = r.response_time_ms;
        
        writeln!(file, "{:<6} {:<40} {:<50} {:<10} {:<8}", 
            r.status_code,
            truncate(&r.target, 40),
            truncate(&r.final_url, 50),
            size,
            time
        )
        .map_err(io_error_to_scout)?;

        // Optional details
        if let Some(ip) = &r.resolved_ip {
            writeln!(file, "       ↳ IP: {}", ip)
                .map_err(io_error_to_scout)?;
        }
        if !r.redirect_chain.is_empty() {
            writeln!(file, "       ↳ Redirects: {}", r.redirect_chain.join(" → "))
                .map_err(io_error_to_scout)?;
        }
        writeln!(file)?; // Empty line between entries
    }

    Ok(())
}

/// Helper: Generate simple status code distribution for JSON metadata
fn generate_status_summary(results: &[ScanResult]) -> serde_json::Value {
    let mut counts = std::collections::HashMap::new();
    for r in results {
        *counts.entry(r.status_code).or_insert(0) += 1;
    }
    serde_json::Value::Object(
        counts.into_iter()
            .map(|(k, v)| (k.to_string(), serde_json::json!(v)))
            .collect()
    )
}

/// Helper: Truncate string for fixed-width columns
fn truncate(s: &str, max_len: usize) -> String {
    if s.len() > max_len {
        format!("{}...", &s[..max_len - 3])
    } else {
        s.to_string()
    }
}

/// Helper: Convert std::io::Error to CyberScoutError
fn io_error_to_scout(e: io::Error) -> CyberScoutError {
    CyberScoutError::OutputWriteError("unknown".into(), e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::NamedTempFile;
    use crate::models::result::{models::status::StatusCategory, ScanType};
    

    fn mock_result(code: u16) -> ScanResult {
        ScanResult {
            id: "test-id".into(),
            target: "test.example.com".into(),
            resolved_ip: Some("1.2.3.4".into()),
            final_url: "https://test.example.com".into(),
            status_code: code,
            status_category: StatusCategory::from(code),
            content_length: Some(1234),
            response_time_ms: 50,
            headers: None,
            redirect_chain: vec![],
            discovered_at: Utc::now(),
            scan_type: ScanType::Subdomain,
            title: None,
        }
    }

    #[test]
    fn test_export_json() -> Result<()> {
        let tmp = NamedTempFile::new()?;
        let results = vec![mock_result(200), mock_result(404)];
        
        save_results(&results, tmp.path())?;
        
        let content = std::fs::read_to_string(tmp.path())?;
        assert!(content.contains("\"total_results\": 2"));
        assert!(content.contains("\"200\": 1"));
        Ok(())
    }

    #[test]
    fn test_export_txt() -> Result<()> {
        let tmp = NamedTempFile::new()?;
        let results = vec![mock_result(200)];
        
        // Force txt extension
        let txt_path = tmp.path().with_extension("txt");
        save_results(&results, &txt_path)?;
        
        let content = std::fs::read_to_string(&txt_path)?;
        assert!(content.contains("STATUS"));
        assert!(content.contains("200"));
        Ok(())
    }
}