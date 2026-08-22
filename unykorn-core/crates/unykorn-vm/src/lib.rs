use borsh::{BorshDeserialize, BorshSerialize};
use unykorn_crypto::{keccak256, Hash256};
use std::collections::BTreeMap;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum VmError {
    #[error("Unauthorized transaction: signature verification failed")]
    InvalidSignature,
    #[error("Insufficient balance for transfer")]
    InsufficientFunds,
    #[error("Nonce mismatch: expected {expected}, got {received}")]
    InvalidNonce { expected: u64, received: u64 },
    #[error("Execution reverted: {0}")]
    ExecutionReverted(String),
}

#[derive(Debug, Clone, BorshSerialize, BorshDeserialize, PartialEq, Eq)]
pub enum Instruction {
    /// Transfer base units
    Transfer { to: [u8; 20], amount: u64 },
    /// Attest RWA collateral state with cryptographic hash
    AttestRwaCollateral { spv_id: [u8; 16], valuation_usd: u64, proof_hash: Hash256 },
    /// Mint permissioned compliance-backed token
    MintToken { recipient: [u8; 20], amount: u64 },
    /// Freeze wallet compliance action
    FreezeAccount { target: [u8; 20] },
}

#[derive(Debug, Clone, BorshSerialize, BorshDeserialize)]
pub struct Transaction {
    pub sender: [u8; 20],
    pub nonce: u64,
    pub instruction: Instruction,
    pub signature: [u8; 64],
}

#[derive(Debug, Clone, Default)]
pub struct WorldState {
    pub accounts: BTreeMap<[u8; 20], AccountState>,
    pub rwa_registry: BTreeMap<[u8; 16], RwaRecord>,
}

#[derive(Debug, Clone, Default, BorshSerialize, BorshDeserialize)]
pub struct AccountState {
    pub balance: u64,
    pub nonce: u64,
    pub is_frozen: bool,
}

#[derive(Debug, Clone, BorshSerialize, BorshDeserialize)]
pub struct RwaRecord {
    pub valuation_usd: u64,
    pub proof_hash: Hash256,
    pub last_updated_timestamp: u64,
}

impl WorldState {
    pub fn new() -> Self {
        Self::default()
    }

    /// Computes the deterministic State Root of the world state
    pub fn compute_state_root(&self) -> Hash256 {
        let mut state_bytes = Vec::new();
        for (addr, acc) in &self.accounts {
            state_bytes.extend_from_slice(addr);
            state_bytes.extend_from_slice(&acc.try_to_vec().unwrap_or_default());
        }
        for (spv, record) in &self.rwa_registry {
            state_bytes.extend_from_slice(spv);
            state_bytes.extend_from_slice(&record.try_to_vec().unwrap_or_default());
        }
        keccak256(&state_bytes)
    }

    /// Deterministically executes a transaction against the state machine
    pub fn apply_transaction(&mut self, tx: &Transaction, current_time: u64) -> Result<(), VmError> {
        let sender_acc = self.accounts.entry(tx.sender).or_default();

        if sender_acc.is_frozen {
            return Err(VmError::ExecutionReverted("Sender account is frozen".into()));
        }

        if tx.nonce != sender_acc.nonce {
            return Err(VmError::InvalidNonce {
                expected: sender_acc.nonce,
                received: tx.nonce,
            });
        }

        match &tx.instruction {
            Instruction::Transfer { to, amount } => {
                if sender_acc.balance < *amount {
                    return Err(VmError::InsufficientFunds);
                }
                sender_acc.balance -= *amount;
                sender_acc.nonce += 1;

                let recipient_acc = self.accounts.entry(*to).or_default();
                recipient_acc.balance += *amount;
            }
            Instruction::AttestRwaCollateral { spv_id, valuation_usd, proof_hash } => {
                sender_acc.nonce += 1;
                self.rwa_registry.insert(*spv_id, RwaRecord {
                    valuation_usd: *valuation_usd,
                    proof_hash: *proof_hash,
                    last_updated_timestamp: current_time,
                });
            }
            Instruction::FreezeAccount { target } => {
                sender_acc.nonce += 1;
                let target_acc = self.accounts.entry(*target).or_default();
                target_acc.is_frozen = true;
            }
            Instruction::MintToken { recipient, amount } => {
                sender_acc.nonce += 1;
                let recipient_acc = self.accounts.entry(*recipient).or_default();
                recipient_acc.balance += *amount;
            }
        }

        Ok(())
    }
}
