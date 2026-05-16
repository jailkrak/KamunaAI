//! HTTP Status Code Categorization
//! 
//! Maps raw HTTP status codes to semantic categories for filtering and coloring.

use serde::{Serialize, Deserialize};
use std::fmt;

/// Semantic category of an HTTP status code
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum StatusCategory {
    /// 2xx: Success
    Success,
    /// 3xx: Redirection
    Redirect,
    /// 4xx: Client Error (e.g., 404, 403)
    ClientError,
    /// 5xx: Server Error
    ServerError,
    /// Network timeout or unresolved DNS
    Timeout,
    /// Other errors
    Error,
}

impl From<u16> for StatusCategory {
    fn from(code: u16) -> Self {
        match code {
            200..=299 => StatusCategory::Success,
            300..=399 => StatusCategory::Redirect,
            400..=499 => StatusCategory::ClientError,
            500..=599 => StatusCategory::ServerError,
            _ => StatusCategory::Error,
        }
    }
}

impl fmt::Display for StatusCategory {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            StatusCategory::Success => write!(f, "Success"),
            StatusCategory::Redirect => write!(f, "Redirect"),
            StatusCategory::ClientError => write!(f, "Client Error"),
            StatusCategory::ServerError => write!(f, "Server Error"),
            StatusCategory::Timeout => write!(f, "Timeout"),
            StatusCategory::Error => write!(f, "Error"),
        }
    }
}

impl StatusCategory {
    /// Returns true if this category is generally considered "interesting" for recon
    pub fn is_interesting(&self) -> bool {
        matches!(
            self,
            StatusCategory::Success | StatusCategory::Redirect | StatusCategory::ClientError
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_status_conversion() {
        assert_eq!(StatusCategory::from(200), StatusCategory::Success);
        assert_eq!(StatusCategory::from(301), StatusCategory::Redirect);
        assert_eq!(StatusCategory::from(404), StatusCategory::ClientError);
        assert_eq!(StatusCategory::from(500), StatusCategory::ServerError);
        assert_eq!(StatusCategory::from(999), StatusCategory::Error);
    }

    #[test]
    fn test_is_interesting() {
        assert!(StatusCategory::Success.is_interesting());
        assert!(StatusCategory::Redirect.is_interesting());
        assert!(StatusCategory::ClientError.is_interesting()); // 403/404 are interesting in recon
        assert!(!StatusCategory::ServerError.is_interesting());
    }
}