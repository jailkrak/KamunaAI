//! Scanner module orchestration
//! 
//! Exports core scanning components and provides clean re-exports
//! for consistent imports across the codebase.

pub mod core;
pub mod directory;
pub mod dns_resolver;
pub mod http_client;
pub mod subdomain;

// Re-export primary scanner types for ergonomic usage in other modules
pub use dns_resolver::DnsResolver;
pub use http_client::AsyncHttpClient;