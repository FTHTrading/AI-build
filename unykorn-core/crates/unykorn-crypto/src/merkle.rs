use sha3::{Digest, Keccak256};
use borsh::{BorshSerialize, BorshDeserialize};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum CryptoError {
    #[error("Serialization failure")]
    SerializationError,
    #[error("Invalid Hash Length")]
    InvalidHashLength,
}

pub type Hash256 = [u8; 32];

pub fn keccak256(data: &[u8]) -> Hash256 {
    let mut hasher = Keccak256::new();
    hasher.update(data);
    hasher.finalize().into()
}

#[derive(Debug, Clone, PartialEq, Eq, BorshSerialize, BorshDeserialize)]
pub struct MerkleNode {
    pub left: Hash256,
    pub right: Hash256,
}

impl MerkleNode {
    pub fn compute_root(left: &Hash256, right: &Hash256) -> Hash256 {
        let mut combined = [0u8; 64];
        combined[..32].copy_from_slice(left);
        combined[32..].copy_from_slice(right);
        keccak256(&combined)
    }
}
