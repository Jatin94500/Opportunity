use std::{process::Command, time::UNIX_EPOCH};

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sysinfo::{ComponentExt, CpuExt, System, SystemExt};

use crate::scheduler::PerformanceMode;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetrySnapshot {
    pub timestamp: DateTime<Utc>,
    pub cpu_load_percent: f32,
    pub cpu_temp_c: f32,
    pub gpu_load_percent: f32,
    pub gpu_temp_c: f32,
    pub net_latency_ms: f32,
    pub earnings_per_sec: f32,
    pub impact_score: f32,
    pub mode: PerformanceMode,
}

pub fn collect_snapshot(mode: PerformanceMode) -> TelemetrySnapshot {
    let mut system = System::new_all();
    system.refresh_all();

    let cpu_load = system.global_cpu_info().cpu_usage().clamp(0.0, 100.0);
    let cpu_temp = read_cpu_temp(&system).unwrap_or_else(|| synthetic_temp(cpu_load, 33.0, 88.0));
    let (gpu_load, gpu_temp) = read_gpu_metrics().unwrap_or_else(|| synthetic_gpu(cpu_load));

    let earnings = ((gpu_load / 100.0) * 0.08).max(0.002);
    let impact_score = ((earnings * 900.0) + ((100.0 - gpu_temp).max(0.0) * 0.8)).max(0.0);
    let latency = synthetic_latency(cpu_load, gpu_load);

    TelemetrySnapshot {
        timestamp: Utc::now(),
        cpu_load_percent: round2(cpu_load),
        cpu_temp_c: round2(cpu_temp),
        gpu_load_percent: round2(gpu_load),
        gpu_temp_c: round2(gpu_temp),
        net_latency_ms: round2(latency),
        earnings_per_sec: round4(earnings),
        impact_score: round2(impact_score),
        mode,
    }
}

fn read_cpu_temp(system: &System) -> Option<f32> {
    let mut hottest = None::<f32>;
    for component in system.components() {
        let value = component.temperature();
        hottest = Some(hottest.map_or(value, |h| h.max(value)));
    }
    hottest
}

fn read_gpu_metrics() -> Option<(f32, f32)> {
    let output = Command::new("nvidia-smi")
        .args([
            "--query-gpu=utilization.gpu,temperature.gpu",
            "--format=csv,noheader,nounits",
        ])
        .output()
        .ok()?;

    if !output.status.success() {
        return None;
    }

    let text = String::from_utf8(output.stdout).ok()?;
    let line = text.lines().next()?;
    let mut parts = line.split(',').map(|p| p.trim());
    let util = parts.next()?.parse::<f32>().ok()?;
    let temp = parts.next()?.parse::<f32>().ok()?;
    Some((util.clamp(0.0, 100.0), temp.clamp(20.0, 100.0)))
}

fn synthetic_gpu(cpu_load: f32) -> (f32, f32) {
    let now = Utc::now()
        .timestamp_nanos_opt()
        .unwrap_or(UNIX_EPOCH.elapsed().unwrap_or_default().as_nanos() as i64);
    let wave = ((now % 11_000_000_000) as f32 / 11_000_000_000.0) * std::f32::consts::TAU;
    let load = (cpu_load * 0.75 + (wave.sin() * 15.0) + 40.0).clamp(5.0, 99.0);
    let temp = synthetic_temp(load, 38.0, 92.0);
    (load, temp)
}

fn synthetic_temp(load: f32, min: f32, max: f32) -> f32 {
    min + ((max - min) * (load / 100.0))
}

fn synthetic_latency(cpu_load: f32, gpu_load: f32) -> f32 {
    (12.0 + (cpu_load * 0.18) + (gpu_load * 0.22)).clamp(8.0, 190.0)
}

fn round2(v: f32) -> f32 {
    (v * 100.0).round() / 100.0
}

fn round4(v: f32) -> f32 {
    (v * 10_000.0).round() / 10_000.0
}

