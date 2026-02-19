use tokio::sync::RwLock;

use crate::{
    config::Config,
    scheduler::{Allocation, PerformanceMode},
    telemetry::TelemetrySnapshot,
};

pub struct RuntimeState {
    pub mode: PerformanceMode,
    pub allocation: Allocation,
    pub telemetry: TelemetrySnapshot,
    pub active_mission: Option<String>,
    pub session_xp: u64,
}

pub struct AppState {
    pub config: Config,
    pub runtime: RwLock<RuntimeState>,
}

impl AppState {
    pub fn new(config: Config, runtime: RuntimeState) -> Self {
        Self {
            config,
            runtime: RwLock::new(runtime),
        }
    }
}

