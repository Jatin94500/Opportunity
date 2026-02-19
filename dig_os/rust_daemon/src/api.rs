use std::sync::Arc;

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use tracing::warn;

use crate::{
    cgroups,
    scheduler::{allocation_for_mode, PerformanceMode},
    state::AppState,
};

pub fn router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/api/v1/telemetry", get(get_telemetry))
        .route("/api/v1/runtime", get(get_runtime))
        .route("/api/v1/mode", post(set_mode))
        .route("/api/v1/missions", get(list_missions))
        .with_state(state)
}

async fn health() -> impl IntoResponse {
    Json(serde_json::json!({
        "status": "ok",
        "service": "dig-rust-daemon",
    }))
}

async fn get_telemetry(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let lock = state.runtime.read().await;
    Json(lock.telemetry.clone())
}

async fn get_runtime(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let lock = state.runtime.read().await;
    Json(RuntimeResponse {
        mode: lock.mode,
        allocation: lock.allocation.clone(),
        active_mission: lock.active_mission.clone(),
        session_xp: lock.session_xp,
    })
}

async fn set_mode(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<ModeRequest>,
) -> impl IntoResponse {
    let mut lock = state.runtime.write().await;
    let allocation = allocation_for_mode(payload.mode, &state.config);
    if let Err(error) = cgroups::apply_allocation(&allocation) {
        warn!("cgroup allocation failed: {error}");
    }

    lock.mode = payload.mode;
    lock.allocation = allocation.clone();

    (
        StatusCode::OK,
        Json(RuntimeResponse {
            mode: lock.mode,
            allocation,
            active_mission: lock.active_mission.clone(),
            session_xp: lock.session_xp,
        }),
    )
}

async fn list_missions() -> impl IntoResponse {
    Json(vec![
        Mission {
            id: "med-pancreas-001".to_string(),
            title: "Pancreatic Cancer Detection".to_string(),
            bounty_dig: 500.0,
            dataset_gb: 4.2,
            eta_minutes: 12,
            priority: 100,
            domain: "medical".to_string(),
        },
        Mission {
            id: "space-exoplanet-004".to_string(),
            title: "Exoplanet Atmosphere Analysis".to_string(),
            bounty_dig: 120.0,
            dataset_gb: 2.1,
            eta_minutes: 7,
            priority: 55,
            domain: "space".to_string(),
        },
        Mission {
            id: "render-cyberpunk-2099".to_string(),
            title: "Render Cyberpunk 2099 Frame".to_string(),
            bounty_dig: 50.0,
            dataset_gb: 1.4,
            eta_minutes: 4,
            priority: 20,
            domain: "render".to_string(),
        },
    ])
}

#[derive(Debug, Deserialize)]
pub struct ModeRequest {
    pub mode: PerformanceMode,
}

#[derive(Debug, Serialize)]
struct RuntimeResponse {
    mode: PerformanceMode,
    allocation: crate::scheduler::Allocation,
    active_mission: Option<String>,
    session_xp: u64,
}

#[derive(Debug, Serialize)]
struct Mission {
    id: String,
    title: String,
    bounty_dig: f32,
    dataset_gb: f32,
    eta_minutes: u16,
    priority: u8,
    domain: String,
}

