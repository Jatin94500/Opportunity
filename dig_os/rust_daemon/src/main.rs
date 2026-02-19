mod api;
mod cgroups;
mod config;
mod scheduler;
mod state;
mod telemetry;

use std::sync::Arc;

use anyhow::Result;
use scheduler::{allocation_for_mode, PerformanceMode};
use tokio::time::{sleep, Duration};
use tracing::{info, warn};

use crate::{config::Config, state::RuntimeState};

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt().with_env_filter("info").init();

    let config = Config::from_env()?;
    let initial_mode = PerformanceMode::Balanced;
    let allocation = allocation_for_mode(initial_mode, &config);
    if let Err(error) = cgroups::apply_allocation(&allocation) {
        warn!("initial cgroups apply failed: {error}");
    }

    let initial_telemetry = telemetry::collect_snapshot(initial_mode);
    let shared = Arc::new(state::AppState::new(
        config.clone(),
        RuntimeState {
            mode: initial_mode,
            allocation,
            telemetry: initial_telemetry,
            active_mission: Some("med-pancreas-001".to_string()),
            session_xp: 0,
        },
    ));

    let worker_state = Arc::clone(&shared);
    tokio::spawn(async move {
        loop {
            let current_mode = {
                let lock = worker_state.runtime.read().await;
                lock.mode
            };
            let snapshot = telemetry::collect_snapshot(current_mode);

            let needs_thermal_throttle = snapshot.gpu_temp_c >= worker_state.config.thermal_limit_c;
            let mut lock = worker_state.runtime.write().await;
            lock.telemetry = snapshot.clone();

            if needs_thermal_throttle && lock.mode != PerformanceMode::Gaming {
                let throttled_mode = PerformanceMode::Balanced;
                lock.mode = throttled_mode;
                lock.allocation = allocation_for_mode(throttled_mode, &worker_state.config);
                if let Err(error) = cgroups::apply_allocation(&lock.allocation) {
                    warn!("thermal cgroups apply failed: {error}");
                }
                warn!(
                    "thermal throttle engaged: gpu={}C limit={}C",
                    snapshot.gpu_temp_c, worker_state.config.thermal_limit_c
                );
            }

            lock.session_xp = lock
                .session_xp
                .saturating_add((snapshot.impact_score / 10.0).max(1.0) as u64);

            sleep(Duration::from_millis(worker_state.config.poll_interval_ms)).await;
        }
    });

    let app = api::router(shared);
    let listener = tokio::net::TcpListener::bind(config.bind_addr).await?;
    info!("dig-rust-daemon listening on {}", config.bind_addr);
    axum::serve(listener, app).await?;
    Ok(())
}

