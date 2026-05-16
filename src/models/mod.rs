//! Data models for CyberScout
//! 
//! Defines the core structures for scan targets, results, and status categorization.
//! Ensures consistent serialization (Serde) and database-like structure for results.

pub mod result;
pub mod status;
pub mod target;

// Re-export primary types for ergonomic imports in other modules
pub use result::ScanResult;
pub use status::StatusCategory;
