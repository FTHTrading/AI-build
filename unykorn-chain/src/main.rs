use chrono::Utc;
use ed25519_dalek::{Signer, SigningKey, VerifyingKey};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::sync::Arc;
use thiserror::Error;
use tokio::sync::RwLock;

// ==========================================
// 1. ERROR TYPES & STATE ENUMS
// ==========================================

#[derive(Error, Debug)]
pub enum ChainError {
    #[error("Invalid Truth Proof: {0}")]
    InvalidTruthProof(String),
    #[error("Invalid State Transition: From {0:?} to {1:?}")]
    InvalidStateTransition(LifelineState, LifelineState),
    #[error("Cryptographic Verification Failed")]
    CryptoError,
    #[error("Zero Balance or Insufficient Permissions")]
    ExecutionDenied,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LifelineState {
    Genesis,
    Bootstrapping,
    AutonomousActive,
    EmergencyQuarantine,
    Halted,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TruthCategory {
    RwaAssetAttestation,
    ComplianceVerification,
    OracleConsensus,
    StateCommitment,
}

// ==========================================
// 2. CRYPTOGRAPHIC DATA STRUCTURES
// ==========================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TruthAttestation {
    pub category: TruthCategory,
    pub claim_hash: String,
    pub confidence_score: u8, // 0 - 100 (Threshold >= 95 for auto-commit)
    pub evidence_uri: String,
    pub signature: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub sender: String,
    pub receiver: String,
    pub payload: String,
    pub truth_proof: TruthAttestation,
    pub nonce: u64,
    pub signature: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Block {
    pub index: u64,
    pub timestamp: i64,
    pub previous_hash: String,
    pub transactions: Vec<Transaction>,
    pub state_root: String,
    pub block_hash: String,
    pub validator_signature: String,
}

impl Block {
    pub fn calculate_hash(
        index: u64,
        timestamp: i64,
        previous_hash: &str,
        transactions: &[Transaction],
        state_root: &str,
    ) -> String {
        let mut hasher = Sha256::new();
        hasher.update(index.to_be_bytes());
        hasher.update(timestamp.to_be_bytes());
        hasher.update(previous_hash.as_bytes());
        let txs_serialized = serde_json::to_string(transactions).unwrap_or_default();
        hasher.update(txs_serialized.as_bytes());
        hasher.update(state_root.as_bytes());
        hex::encode(hasher.finalize())
    }
}

// ==========================================
// 3. AUTONOMOUS STATE MACHINE & LEDGER
// ==========================================

pub struct UnykornChainState {
    pub lifeline_state: LifelineState,
    pub block_height: u64,
    pub state_registry: HashMap<String, String>,
    pub chain: Vec<Block>,
    pub pending_mempool: Vec<Transaction>,
    signing_key: SigningKey,
    pub verifying_key: VerifyingKey,
}

impl UnykornChainState {
    pub fn new() -> Self {
        let mut rng = rand::thread_rng();
        let signing_key = SigningKey::generate(&mut rng);
        let verifying_key = signing_key.verifying_key();

        let genesis_block = Block {
            index: 0,
            timestamp: Utc::now().timestamp(),
            previous_hash: "0000000000000000000000000000000000000000000000000000000000000000".to_string(),
            transactions: vec![],
            state_root: "GENESIS_ROOT_UNYKORN_LLC".to_string(),
            block_hash: "0000000000000000000000000000000000000000000000000000000000000000".to_string(),
            validator_signature: "GENESIS_SIG".to_string(),
        };

        Self {
            lifeline_state: LifelineState::Genesis,
            block_height: 0,
            state_registry: HashMap::new(),
            chain: vec![genesis_block],
            pending_mempool: vec![],
            signing_key,
            verifying_key,
        }
    }

    pub fn transition_lifeline(&mut self, target: LifelineState) -> Result<(), ChainError> {
        match (self.lifeline_state, target) {
            (LifelineState::Genesis, LifelineState::Bootstrapping) => {
                self.lifeline_state = LifelineState::Bootstrapping;
            }
            (LifelineState::Bootstrapping, LifelineState::AutonomousActive) => {
                self.lifeline_state = LifelineState::AutonomousActive;
            }
            (LifelineState::AutonomousActive, LifelineState::EmergencyQuarantine) => {
                self.lifeline_state = LifelineState::EmergencyQuarantine;
            }
            (LifelineState::EmergencyQuarantine, LifelineState::AutonomousActive) => {
                self.lifeline_state = LifelineState::AutonomousActive;
            }
            (_, LifelineState::Halted) => {
                self.lifeline_state = LifelineState::Halted;
            }
            (from, to) => return Err(ChainError::InvalidStateTransition(from, to)),
        }
        tracing::info!("[*] Lifeline Transition: -> {:?}", self.lifeline_state);
        Ok(())
    }

    pub fn submit_transaction(&mut self, tx: Transaction) -> Result<(), ChainError> {
        if self.lifeline_state != LifelineState::AutonomousActive {
            return Err(ChainError::ExecutionDenied);
        }

        // Truth validation check: Must score >= 95 confidence
        if tx.truth_proof.confidence_score < 95 {
            return Err(ChainError::InvalidTruthProof(format!(
                "Confidence score {} is below mandatory threshold 95",
                tx.truth_proof.confidence_score
            )));
        }

        self.pending_mempool.push(tx);
        Ok(())
    }

    pub fn produce_block(&mut self) -> Result<Block, ChainError> {
        if self.lifeline_state != LifelineState::AutonomousActive {
            return Err(ChainError::ExecutionDenied);
        }

        let previous_block = self.chain.last().unwrap();
        let current_index = previous_block.index + 1;
        let current_timestamp = Utc::now().timestamp();

        // Apply transactions to state machine
        for tx in &self.pending_mempool {
            self.state_registry.insert(tx.sender.clone(), tx.payload.clone());
        }

        // Calculate dynamic State Root
        let mut hasher = Sha256::new();
        for (k, v) in &self.state_registry {
            hasher.update(k.as_bytes());
            hasher.update(v.as_bytes());
        }
        let state_root = hex::encode(hasher.finalize());

        let block_hash = Block::calculate_hash(
            current_index,
            current_timestamp,
            &previous_block.block_hash,
            &self.pending_mempool,
            &state_root,
        );

        // Sign block with autonomous AI key
        let signature = self.signing_key.sign(block_hash.as_bytes());
        let signature_hex = hex::encode(signature.to_bytes());

        let new_block = Block {
            index: current_index,
            timestamp: current_timestamp,
            previous_hash: previous_block.block_hash.clone(),
            transactions: self.pending_mempool.drain(..).collect(),
            state_root,
            block_hash,
            validator_signature: signature_hex,
        };

        self.chain.push(new_block.clone());
        self.block_height = current_index;

        tracing::info!(
            "[+] Block #{} Produced & Finalized | Hash: {} | State Root: {}",
            new_block.index,
            &new_block.block_hash[0..16],
            &new_block.state_root[0..16]
        );

        Ok(new_block)
    }
}

// ==========================================
// 4. AUTONOMOUS RUNTIME LIFELINE LOOP
// ==========================================

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();
    tracing::info!("=== UNYKORN AUTONOMOUS NEURAL CHAIN RUNTIME ===");

    let chain_engine = Arc::new(RwLock::new(UnykornChainState::new()));

    // 1. Bootstrapping Lifeline
    {
        let mut engine = chain_engine.write().await;
        engine.transition_lifeline(LifelineState::Bootstrapping)?;
        engine.transition_lifeline(LifelineState::AutonomousActive)?;
    }

    // 2. Simulate Ingestion of High-Confidence Truth Attestation
    let dummy_tx = Transaction {
        sender: "0xUNYKORN_TREASURY_GATEWAY".to_string(),
        receiver: "0xSPV_SENIOR_DEBT_FACILITY_1".to_string(),
        payload: "SET_AUC_VALUE=$4,820,000,000; VERIFIED_ASSETS=155".to_string(),
        truth_proof: TruthAttestation {
            category: TruthCategory::RwaAssetAttestation,
            claim_hash: "0x98f234abcd09123847aefbcde09812".to_string(),
            confidence_score: 99,
            evidence_uri: "obsidian://03_ASSET_REGISTRIES/SPV_STRUCTURES.md".to_string(),
            signature: "0xAI_SIGNATURE_PROOF".to_string(),
        },
        nonce: 1,
        signature: "0xTX_SIGNATURE".to_string(),
    };

    // 3. Ingest & Arbitrate Block Production
    {
        let mut engine = chain_engine.write().await;
        engine.submit_transaction(dummy_tx)?;
        let block = engine.produce_block()?;
        tracing::info!("[*] Block Transactions: {:?}", block.transactions.len());
    }

    // 4. Background Autonomous Heartbeat Loop
    let engine_clone = Arc::clone(&chain_engine);
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(5));
        loop {
            interval.tick().await;
            let mut engine = engine_clone.write().await;
            if engine.lifeline_state == LifelineState::AutonomousActive {
                if !engine.pending_mempool.is_empty() {
                    let _ = engine.produce_block();
                } else {
                    tracing::debug!("[Heartbeat] Lifeline: Active | Block Height: {}", engine.block_height);
                }
            }
        }
    });

    // Keep active
    tokio::time::sleep(tokio::time::Duration::from_secs(6)).await;
    tracing::info!("[+] Unykorn Neural Chain state machine online and autonomous.");

    Ok(())
}
