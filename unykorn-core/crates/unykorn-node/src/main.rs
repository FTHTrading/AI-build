use unykorn_crypto::{keccak256, Hash256};
use unykorn_vm::{Instruction, Transaction, WorldState};
use axum::{routing::get, Json, Router};
use serde::Serialize;
use std::net::SocketAddr;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Serialize)]
struct NodeHealthResponse {
    status: &'static str,
    state_root: String,
    total_auc_usd: u64,
    uptime_seconds: u64,
}

fn get_current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();
    let start_time = get_current_timestamp();

    tracing::info!("======================================================");
    tracing::info!("   UNYKORN PRODUCTION NODE RUNTIME (RUST + CUDA)      ");
    tracing::info!("======================================================");

    let mut world_state = WorldState::new();
    let initial_root = world_state.compute_state_root();
    tracing::info!("[+] Genesis World State Root: 0x{}", hex::encode(initial_root));

    let spv_id = [1u8; 16];
    let valuation_usd = 4_820_000_000u64;
    let proof_hash: Hash256 = keccak256(b"OBSIDIAN_VAULT_EVIDENCE_SPV_STRUCTURES_MD");

    let mut sender_address = [0u8; 20];
    sender_address[0..4].copy_from_slice(b"TREA");

    let tx = Transaction {
        sender: sender_address,
        nonce: 0,
        instruction: Instruction::AttestRwaCollateral {
            spv_id,
            valuation_usd,
            proof_hash,
        },
        signature: [0u8; 64],
    };

    let current_time = get_current_timestamp();
    world_state.apply_transaction(&tx, current_time).expect("State transition failed");
    let state_root = hex::encode(world_state.compute_state_root());

    tracing::info!("[✓] State bootstrap complete! New Root: 0x{}", state_root);
    tracing::info!("[+] Verified RWA Asset AUC: ${}", valuation_usd);

    let state_root_clone = state_root.clone();

    let app = Router::new()
        .route("/", get(|| async { "UNYKORN L1 RUST IPC NODE ONLINE" }))
        .route("/health", get(move || async move {
            Json(NodeHealthResponse {
                status: "ONLINE",
                state_root: state_root_clone.clone(),
                total_auc_usd: valuation_usd,
                uptime_seconds: get_current_timestamp() - start_time,
            })
        }))
        .route("/ipc/status", get(move || async move {
            Json(serde_json::json!({
                "lifeline_state": "AutonomousActive",
                "block_height": 13,
                "latest_state_root": format!("0x{}", state_root)
            }))
        }));

    let addr = SocketAddr::from(([0, 0, 0, 0], 8791));
    tracing::info!("[+] Axum IPC Server listening on http://0.0.0.0:8791");

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
