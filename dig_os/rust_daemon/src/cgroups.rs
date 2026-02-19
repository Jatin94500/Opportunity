use std::{fs, path::Path};

use anyhow::Result;
use tracing::warn;

use crate::scheduler::Allocation;

const CGROUP_ROOT: &str = "/sys/fs/cgroup";
const UI_GROUP: &str = "dig-ui";
const WORKER_GROUP: &str = "dig-worker";
const CGROUP_PERIOD_US: u32 = 100_000;

pub fn apply_allocation(allocation: &Allocation) -> Result<()> {
    #[cfg(target_os = "linux")]
    {
        let ui_dir = Path::new(CGROUP_ROOT).join(UI_GROUP);
        let worker_dir = Path::new(CGROUP_ROOT).join(WORKER_GROUP);

        fs::create_dir_all(&ui_dir)?;
        fs::create_dir_all(&worker_dir)?;

        write_cpu_limits(&ui_dir, allocation.ui_cpu_percent)?;
        write_cpu_limits(&worker_dir, allocation.worker_cpu_percent)?;
    }

    #[cfg(not(target_os = "linux"))]
    {
        warn!("cgroups v2 apply skipped: host is not linux");
    }

    Ok(())
}

#[cfg(target_os = "linux")]
fn write_cpu_limits(dir: &Path, percent: u8) -> Result<()> {
    let pct = percent.clamp(1, 100) as u32;
    let quota = (CGROUP_PERIOD_US * pct) / 100;
    let cpu_max = format!("{quota} {CGROUP_PERIOD_US}");
    let cpu_weight = (((pct as f32 / 100.0) * 9900.0) + 100.0).round() as u32;

    write_if_exists(&dir.join("cpu.max"), &cpu_max);
    write_if_exists(&dir.join("cpu.weight"), &cpu_weight.to_string());
    Ok(())
}

#[cfg(target_os = "linux")]
fn write_if_exists(path: &Path, value: &str) {
    if path.exists() {
        if let Err(error) = fs::write(path, value) {
            warn!("failed to write {}: {error}", path.display());
        }
    }
}

