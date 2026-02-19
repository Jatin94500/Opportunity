use std::{env, net::SocketAddr};

use anyhow::{anyhow, Result};

#[derive(Debug, Clone)]
pub struct Config {
    pub bind_addr: SocketAddr,
    pub poll_interval_ms: u64,
    pub thermal_limit_c: f32,
    pub ui_reserved_cpu_percent: u8,
    pub ui_reserved_gpu_percent: u8,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            bind_addr: "127.0.0.1:7788".parse().expect("valid socket"),
            poll_interval_ms: 1000,
            thermal_limit_c: 85.0,
            ui_reserved_cpu_percent: 5,
            ui_reserved_gpu_percent: 5,
        }
    }
}

impl Config {
    pub fn from_env() -> Result<Self> {
        let mut cfg = Self::default();

        if let Ok(value) = env::var("DIG_DAEMON_ADDR") {
            cfg.bind_addr = value
                .parse()
                .map_err(|_| anyhow!("invalid DIG_DAEMON_ADDR: {value}"))?;
        }
        if let Ok(value) = env::var("DIG_POLL_INTERVAL_MS") {
            cfg.poll_interval_ms = value
                .parse()
                .map_err(|_| anyhow!("invalid DIG_POLL_INTERVAL_MS: {value}"))?;
        }
        if let Ok(value) = env::var("DIG_THERMAL_LIMIT_C") {
            cfg.thermal_limit_c = value
                .parse()
                .map_err(|_| anyhow!("invalid DIG_THERMAL_LIMIT_C: {value}"))?;
        }
        if let Ok(value) = env::var("DIG_UI_RESERVED_CPU_PERCENT") {
            cfg.ui_reserved_cpu_percent = value
                .parse()
                .map_err(|_| anyhow!("invalid DIG_UI_RESERVED_CPU_PERCENT: {value}"))?;
        }
        if let Ok(value) = env::var("DIG_UI_RESERVED_GPU_PERCENT") {
            cfg.ui_reserved_gpu_percent = value
                .parse()
                .map_err(|_| anyhow!("invalid DIG_UI_RESERVED_GPU_PERCENT: {value}"))?;
        }

        Ok(cfg)
    }
}

