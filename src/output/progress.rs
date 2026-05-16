use indicatif::{ProgressBar, ProgressStyle};
use std::time::Duration;
use crate::config::OutputConfig;

pub struct ProgressManager {
    pb: Option<ProgressBar>,
    #[allow(dead_code)]
    enabled: bool,
}

impl ProgressManager {

    pub fn new(config: &OutputConfig, total: u64) -> Self {
        if !config.show_progress {
            return Self {
                pb: None,
                enabled: false,
            };
        }

        let pb = ProgressBar::new(total);

        pb.set_style(
            ProgressStyle::with_template(
                "{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta}) {msg}"
            )
            .unwrap()
            .progress_chars("#>-"),
        );

        pb.enable_steady_tick(Duration::from_millis(100));

        Self {
            pb: Some(pb),
            enabled: true,
        }
    }

    pub fn inc(&self) {
        if let Some(pb) = &self.pb {
            pb.inc(1);
        }
    }

    // FIX: lifetime-safe
    pub fn set_message(&self, msg: impl Into<String>) {
        if let Some(pb) = &self.pb {
            pb.set_message(msg.into());
        }
    }

    pub fn finish(&self) {
        if let Some(pb) = &self.pb {
            pb.finish_with_message("Scan Complete!");
        }
    }

    pub fn abandon(&self) {
        if let Some(pb) = &self.pb {
            pb.abandon_with_message("Scan Aborted");
        }
    }
}

impl Drop for ProgressManager {
    fn drop(&mut self) {
        if let Some(pb) = &self.pb {
            pb.finish_and_clear();
        }
    }
}