use unykorn_crypto::{keccak256, Hash256};
use unykorn_vm::{Instruction, Transaction, WorldState};
use std::time::{SystemTime, UNIX_EPOCH};

fn get_current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();
    tracing::info!("======================================================");
    tracing::info!("   UNYKORN PRODUCTION NODE RUNTIME (RUST + CUDA)      ");
    tracing::info!("======================================================");

    // 1. Initialize Deterministic World State
    let mut world_state = WorldState::new();
    let initial_root = world_state.compute_state_root();
    tracing::info!("[+] Genesis World State Root: 0x{}", hex::encode(initial_root));

    // 2. Prepare Sample RWA Collateral Attestation Instruction
    let spv_id = [1u8; 16]; // SPV-1 Identifier
    let valuation_usd = 4_820_000_000u64; // $4.82B USD AUC
    let proof_hash: Hash256 = keccak256(b"OBSIDIAN_VAULT_EVIDENCE_SPV_STRUCTURES_MD");

    let mut sender_address = [0u8; 20];
    sender_address[0..4].copy_from_slice(b"TREA"); // 0x54524541... (Treasury Gateway)

    let tx = Transaction {
        sender: sender_address,
        nonce: 0,
        instruction: Instruction::AttestRwaCollateral {
            spv_id,
            valuation_usd,
            proof_hash,
        },
        signature: [0u8; 64], // Simulated Ed25519 signature
    };

    // 3. Execute Deterministic State Transition
    let current_time = get_current_timestamp();
    match world_state.apply_transaction(&tx, current_time) {
        Ok(_) => {
            let updated_root = world_state.compute_state_root();
            tracing::info!("[✓] Transaction applied successfully via unykorn-vm!");
            tracing::info!("[+] New State Root: 0x{}", hex::encode(updated_root));
            tracing::info!("[+] Verified RWA Asset AUC: ${}", valuation_usd);
        }
        Err(e) => {
            tracing::error!("[!] State transition reverted: {:?}", e);
        }
    }

    Ok(())
}
