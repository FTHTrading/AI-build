mod storage;

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use chrono::Utc;
use ed25519_dalek::{Signer, SigningKey, VerifyingKey};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::Arc;
use storage::ChainDb;
use thiserror::Error;
use tokio::sync::RwLock;
use tower_http::cors::CorsLayer;

#[derive(Error, Debug)]
pub enum ChainError {
    #[error("Invalid Truth Proof: {0}")]
    InvalidTruthProof(String),
    #[error("Invalid State Transition: From {0:?} to {1:?}")]
    InvalidStateTransition(LifelineState, LifelineState),
    #[error("Zero Balance or Insufficient Permissions")]
    ExecutionDenied,
    #[error("Storage Failure: {0}")]
    StorageError(String),
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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TruthAttestation {
    pub category: TruthCategory,
    pub claim_hash: String,
    pub confidence_score: u8,
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

pub struct UnykornChainState {
    pub lifeline_state: LifelineState,
    pub block_height: u64,
    pub state_registry: HashMap<String, String>,
    pub chain: Vec<Block>,
    pub pending_mempool: Vec<Transaction>,
    signing_key: SigningKey,
    pub verifying_key: VerifyingKey,
    pub db: ChainDb,
}

impl UnykornChainState {
    pub fn new(db_path: &str) -> Result<Self, ChainError> {
        let mut rng = rand::thread_rng();
        let signing_key = SigningKey::generate(&mut rng);
        let verifying_key = signing_key.verifying_key();
        let db = ChainDb::open(db_path)?;

        let loaded_chain = db.load_full_chain()?;
        let (chain, height) = if loaded_chain.is_empty() {
            let genesis_block = Block {
                index: 0,
                timestamp: Utc::now().timestamp(),
                previous_hash: "0000000000000000000000000000000000000000000000000000000000000000".to_string(),
                transactions: vec![],
                state_root: "GENESIS_ROOT_UNYKORN_LLC".to_string(),
                block_hash: "0000000000000000000000000000000000000000000000000000000000000000".to_string(),
                validator_signature: "GENESIS_SIG".to_string(),
            };
            db.put_block(&genesis_block)?;
            (vec![genesis_block], 0)
        } else {
            let top_height = loaded_chain.last().unwrap().index;
            (loaded_chain, top_height)
        };

        Ok(Self {
            lifeline_state: LifelineState::Genesis,
            block_height: height,
            state_registry: HashMap::new(),
            chain,
            pending_mempool: vec![],
            signing_key,
            verifying_key,
            db,
        })
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

        for tx in &self.pending_mempool {
            self.state_registry.insert(tx.sender.clone(), tx.payload.clone());
            self.db.put_state_entry(&tx.sender, &tx.payload)?;
        }

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

        self.db.put_block(&new_block)?;
        self.chain.push(new_block.clone());
        self.block_height = current_index;

        tracing::info!(
            "[+] Block #{} Produced & Persisted | Hash: {} | State Root: {}",
            new_block.index,
            &new_block.block_hash[0..16],
            &new_block.state_root[0..16]
        );

        Ok(new_block)
    }
}

// --- IPC API SCHEMAS ---
#[derive(Serialize)]
struct ChainStatusResponse {
    lifeline_state: LifelineState,
    block_height: u64,
    mempool_size: usize,
    latest_state_root: String,
}

#[derive(Serialize)]
struct GenericResponse {
    success: bool,
    message: String,
}

// --- IPC ROUTE HANDLERS ---
async fn get_status(State(engine): State<Arc<RwLock<UnykornChainState>>>) -> impl IntoResponse {
    let state = engine.read().await;
    let latest_root = state.chain.last().map(|b| b.state_root.clone()).unwrap_or_default();
    
    Json(ChainStatusResponse {
        lifeline_state: state.lifeline_state,
        block_height: state.block_height,
        mempool_size: state.pending_mempool.len(),
        latest_state_root: latest_root,
    })
}

async fn post_transaction(
    State(engine): State<Arc<RwLock<UnykornChainState>>>,
    Json(tx): Json<Transaction>,
) -> impl IntoResponse {
    let mut state = engine.write().await;
    match state.submit_transaction(tx) {
        Ok(_) => (
            StatusCode::OK,
            Json(GenericResponse {
                success: true,
                message: "Transaction accepted into mempool".to_string(),
            }),
        ),
        Err(e) => (
            StatusCode::BAD_REQUEST,
            Json(GenericResponse {
                success: false,
                message: format!("Submission rejected: {e}"),
            }),
        ),
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();
    tracing::info!("=== UNYKORN AUTONOMOUS NEURAL CHAIN (IPC PORT 8791) ===");

    let db_path = r"C:\Unykorn-Brain\.rocksdb_chain";
    let chain_engine = Arc::new(RwLock::new(UnykornChainState::new(db_path)?));

    {
        let mut engine = chain_engine.write().await;
        engine.transition_lifeline(LifelineState::Bootstrapping)?;
        engine.transition_lifeline(LifelineState::AutonomousActive)?;
    }

    // Attach Axum IPC server on port 8791
    let app = Router::new()
        .route("/ipc/status", get(get_status))
        .route("/ipc/tx", post(post_transaction))
        .layer(CorsLayer::permissive())
        .with_state(Arc::clone(&chain_engine));

    let addr = SocketAddr::from(([127, 0, 0, 1], 8791));
    tokio::spawn(async move {
        let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
        tracing::info!("[+] Embedded IPC Server listening on http://{}", addr);
        axum::serve(listener, app).await.unwrap();
    });

    let engine_clone = Arc::clone(&chain_engine);
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(5));
        loop {
            interval.tick().await;
            let mut engine = engine_clone.write().await;
            if engine.lifeline_state == LifelineState::AutonomousActive {
                if !engine.pending_mempool.is_empty() {
                    let _ = engine.produce_block();
                }
            }
        }
    });

    tokio::time::sleep(tokio::time::Duration::from_secs(6)).await;
    tracing::info!("[+] Unykorn Neural Chain state machine online and autonomous.");

    Ok(())
}
