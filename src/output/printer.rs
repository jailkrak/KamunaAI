//! Terminal Output Printer
//!
//! Pretty-print scan results with optional ANSI coloring.

use colored::*;
use crate::models::{ScanResult, StatusCategory};

pub struct TerminalPrinter {
    colored: bool,
}

impl TerminalPrinter {
    pub fn new(no_color: bool) -> Self {
        Self {
            colored: !no_color,
        }
    }

    /// Show startup banner
    pub fn banner(&self) {
        if self.colored {
            println!(
                "{}",
                r#"
=========================================
            PENTINEL-WORKER
            BY PENTINEL APEX
            VERSION 1.0
=========================================
"#
                .cyan()
                .bold()
            );
        } else {
            println!("\nPENTINEL-WORKER\n");
        }
    }

    /// Print successful finding
    pub fn found(&self, result: &ScanResult) {
        let status = self.format_status(
            result.status_code,
            &result.status_category,
        );

        let url = if self.colored {
            result.final_url.blue().to_string()
        } else {
            result.final_url.clone()
        };

        println!(
            "[{}] {} {} ({})",
            self.format_time(result.response_time_ms),
            status,
            url,
            result
                .content_length
                .map(|s| format!("{}B", s))
                .unwrap_or_else(|| "-".into())
        );
    }

    /// Print error
    pub fn error(&self, target: &str, err: &str) {
        let target_text = if self.colored {
            target.red().to_string()
        } else {
            target.to_string()
        };

        let err_text = if self.colored {
            err.dimmed().to_string()
        } else {
            err.to_string()
        };

        eprintln!("[✗] {} - {}", target_text, err_text);
    }

    /// Print success message
    pub fn success(&self, msg: &str) {
        if self.colored {
            println!("[✓] {}", msg.green());
        } else {
            println!("[✓] {}", msg);
        }
    }

    /// Informational message
    pub fn info(&self, msg: &str) {
        if self.colored {
            println!("[*] {}", msg.cyan());
        } else {
            println!("[*] {}", msg);
        }
    }

    /// Warning message
    pub fn warning(&self, msg: &str) {
        if self.colored {
            println!("[!] {}", msg.yellow());
        } else {
            println!("[!] {}", msg);
        }
    }

    /// Print summary report
    pub fn summary(&self, results: &[ScanResult]) {
        let total = results.len();

        let by_status = self.group_by_status(results);

        println!("\n{}", "=".repeat(50));

        if self.colored {
            println!("{}", "[+] PENTINEL-WORKER SUMMARY".bold());
        } else {
            println!("[+] PENTINEL-WORKER SUMMARY");
        }

        println!("{}", "=".repeat(50));

        println!("Total found: {}", total);

        for (category, count) in by_status {
            let label = match category {
                StatusCategory::Success => {
                    if self.colored {
                        "✓ 2xx".green().to_string()
                    } else {
                        "✓ 2xx".to_string()
                    }
                }

                StatusCategory::Redirect => {
                    if self.colored {
                        "↻ 3xx".yellow().to_string()
                    } else {
                        "↻ 3xx".to_string()
                    }
                }

                StatusCategory::ClientError => {
                    if self.colored {
                        "⚠ 4xx".yellow().to_string()
                    } else {
                        "⚠ 4xx".to_string()
                    }
                }

                StatusCategory::ServerError => {
                    if self.colored {
                        "✗ 5xx".red().to_string()
                    } else {
                        "✗ 5xx".to_string()
                    }
                }

                _ => {
                    if self.colored {
                        "? Other".dimmed().to_string()
                    } else {
                        "? Other".to_string()
                    }
                }
            };

            println!("  {}: {}", label, count);
        }

        println!("{}", "=".repeat(50));
    }

    /// Format status code with color
    fn format_status(
        &self,
        code: u16,
        category: &StatusCategory,
    ) -> colored::ColoredString {
        let text = format!("{:3}", code);

        if !self.colored {
            return text.normal();
        }

        match category {
            StatusCategory::Success => text.green().bold(),
            StatusCategory::Redirect => text.yellow().bold(),
            StatusCategory::ClientError => {
                text.on_yellow().black().bold()
            }
            StatusCategory::ServerError => text.red().bold(),
            _ => text.dimmed().bold(),
        }
    }

    /// Format response time
    fn format_time(&self, ms: u64) -> String {
        let text = format!("{:3}ms", ms);

        if !self.colored {
            return text;
        }

        if ms < 100 {
            text.green().to_string()
        } else if ms < 500 {
            text.yellow().to_string()
        } else {
            text.red().to_string()
        }
    }

    /// Group results by status category
    fn group_by_status(
        &self,
        results: &[ScanResult],
    ) -> Vec<(StatusCategory, usize)> {
        use std::collections::HashMap;

        let mut map = HashMap::new();

        for r in results {
            *map.entry(r.status_category.clone())
                .or_insert(0) += 1;
        }

        let mut vec: Vec<_> = map.into_iter().collect();

        vec.sort_by_key(|(cat, _)| match cat {
            StatusCategory::Success => 0,
            StatusCategory::Redirect => 1,
            StatusCategory::ClientError => 2,
            StatusCategory::ServerError => 3,
            _ => 4,
        });

        vec
    }
}