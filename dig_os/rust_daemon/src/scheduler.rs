use serde::{Deserialize, Serialize};

use crate::config::Config;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum PerformanceMode {
    Gaming,
    Balanced,
    Sleep,
    Autopilot,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Allocation {
    pub ui_cpu_percent: u8,
    pub worker_cpu_percent: u8,
    pub ui_gpu_percent: u8,
    pub worker_gpu_percent: u8,
    pub profile: &'static str,
}

pub fn allocation_for_mode(mode: PerformanceMode, cfg: &Config) -> Allocation {
    match mode {
        PerformanceMode::Gaming => Allocation {
            ui_cpu_percent: cfg.ui_reserved_cpu_percent.max(15),
            worker_cpu_percent: 20,
            ui_gpu_percent: cfg.ui_reserved_gpu_percent.max(20),
            worker_gpu_percent: 10,
            profile: "gaming",
        },
        PerformanceMode::Sleep => Allocation {
            ui_cpu_percent: cfg.ui_reserved_cpu_percent.max(3),
            worker_cpu_percent: 95,
            ui_gpu_percent: cfg.ui_reserved_gpu_percent.max(2),
            worker_gpu_percent: 98,
            profile: "sleep",
        },
        PerformanceMode::Autopilot => Allocation {
            ui_cpu_percent: cfg.ui_reserved_cpu_percent.max(5),
            worker_cpu_percent: 85,
            ui_gpu_percent: cfg.ui_reserved_gpu_percent.max(5),
            worker_gpu_percent: 90,
            profile: "autopilot",
        },
        PerformanceMode::Balanced => Allocation {
            ui_cpu_percent: cfg.ui_reserved_cpu_percent.max(5),
            worker_cpu_percent: 80,
            ui_gpu_percent: cfg.ui_reserved_gpu_percent.max(5),
            worker_gpu_percent: 85,
            profile: "balanced",
        },
    }
}

