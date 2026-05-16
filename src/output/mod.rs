//! Output module orchestration
//! 
//! Handles all user-facing output: terminal printing, progress bars, 
//! and file exporting (JSON/TXT).

pub mod exporter;
pub mod printer;
pub mod progress;

// Re-export primary types for ergonomic usage in main.rs
pub use exporter::save_results;
pub use printer::TerminalPrinter;
