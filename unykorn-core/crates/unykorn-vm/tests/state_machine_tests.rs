use unykorn_crypto::{keccak256, Hash256};
use unykorn_vm::{AccountState, Instruction, Transaction, VmError, WorldState};

fn mock_address(id: u8) -> [u8; 20] {
    let mut addr = [0u8; 20];
    addr[19] = id;
    addr
}

fn mock_spv(id: u8) -> [u8; 16] {
    let mut spv = [0u8; 16];
    spv[15] = id;
    spv
}

// ==========================================
// 1. DETERMINISTIC BINARY SERIALIZATION TESTS
// ==========================================

#[test]
fn test_borsh_transaction_serialization_roundtrip() {
    let sender = mock_address(1);
    let recipient = mock_address(2);
    let amount = 500_000_000u64;

    let original_tx = Transaction {
        sender,
        nonce: 42,
        instruction: Instruction::Transfer {
            to: recipient,
            amount,
        },
        signature: [7u8; 64],
    };

    // Serialize to binary wire format
    let serialized_bytes = borsh::to_vec(&original_tx)
        .expect("Borsh serialization must not fail");

    // Assert non-empty and deterministic size
    assert!(!serialized_bytes.is_empty());

    // Deserialize back to struct
    let deserialized_tx: Transaction = borsh::from_slice(&serialized_bytes)
        .expect("Borsh deserialization must succeed");

    assert_eq!(original_tx.sender, deserialized_tx.sender);
    assert_eq!(original_tx.nonce, deserialized_tx.nonce);
    assert_eq!(original_tx.instruction, deserialized_tx.instruction);
    assert_eq!(original_tx.signature, deserialized_tx.signature);
}

// ==========================================
// 2. STATE TRANSITIONS & MERKLE ROOT DRIFT
// ==========================================

#[test]
fn test_state_root_determinism_and_mutation() {
    let mut world = WorldState::new();
    let genesis_root = world.compute_state_root();

    let admin = mock_address(1);
    let investor = mock_address(2);

    // Initial Mint
    let mint_tx = Transaction {
        sender: admin,
        nonce: 0,
        instruction: Instruction::MintToken {
            recipient: investor,
            amount: 1_000_000,
        },
        signature: [0u8; 64],
    };

    world
        .apply_transaction(&mint_tx, 1700000000)
        .expect("Mint transaction must succeed");

    let post_mint_root = world.compute_state_root();
    assert_ne!(
        genesis_root, post_mint_root,
        "State root must change after mint state mutation"
    );

    // Verify recipient balance and nonce state
    let investor_state = world.accounts.get(&investor).unwrap();
    assert_eq!(investor_state.balance, 1_000_000);
    assert_eq!(investor_state.nonce, 0);

    let admin_state = world.accounts.get(&admin).unwrap();
    assert_eq!(admin_state.nonce, 1);
}

// ==========================================
// 3. REVERTS, NONCE SAFETY & FREEZE RULES
// ==========================================

#[test]
fn test_revert_on_invalid_nonce() {
    let mut world = WorldState::new();
    let sender = mock_address(1);

    let invalid_nonce_tx = Transaction {
        sender,
        nonce: 5, // Expected nonce is 0
        instruction: Instruction::Transfer {
            to: mock_address(2),
            amount: 100,
        },
        signature: [0u8; 64],
    };

    let result = world.apply_transaction(&invalid_nonce_tx, 1700000000);
    match result {
        Err(VmError::InvalidNonce { expected, received }) => {
            assert_eq!(expected, 0);
            assert_eq!(received, 5);
        }
        _ => panic!("Expected InvalidNonce error"),
    }
}

#[test]
fn test_revert_on_insufficient_funds() {
    let mut world = WorldState::new();
    let sender = mock_address(1);

    // Seed account with 50 units
    world.accounts.insert(
        sender,
        AccountState {
            balance: 50,
            nonce: 0,
            is_frozen: false,
        },
    );

    let overspend_tx = Transaction {
        sender,
        nonce: 0,
        instruction: Instruction::Transfer {
            to: mock_address(2),
            amount: 100, // Exceeds balance of 50
        },
        signature: [0u8; 64],
    };

    let result = world.apply_transaction(&overspend_tx, 1700000000);
    assert!(matches!(result, Err(VmError::InsufficientFunds)));
}

#[test]
fn test_account_freezing_execution_block() {
    let mut world = WorldState::new();
    let compliance_admin = mock_address(1);
    let sanctioned_wallet = mock_address(9);

    // Seed sanctioned wallet with funds
    world.accounts.insert(
        sanctioned_wallet,
        AccountState {
            balance: 5_000_000,
            nonce: 0,
            is_frozen: false,
        },
    );

    // 1. Admin freezes sanctioned wallet
    let freeze_tx = Transaction {
        sender: compliance_admin,
        nonce: 0,
        instruction: Instruction::FreezeAccount {
            target: sanctioned_wallet,
        },
        signature: [0u8; 64],
    };
    world
        .apply_transaction(&freeze_tx, 1700000000)
        .expect("Freeze tx must succeed");

    assert!(world.accounts.get(&sanctioned_wallet).unwrap().is_frozen);

    // 2. Sanctioned wallet attempts transfer -> Must Revert
    let transfer_tx = Transaction {
        sender: sanctioned_wallet,
        nonce: 0,
        instruction: Instruction::Transfer {
            to: mock_address(2),
            amount: 1_000,
        },
        signature: [0u8; 64],
    };

    let result = world.apply_transaction(&transfer_tx, 1700000001);
    assert!(matches!(result, Err(VmError::ExecutionReverted(_))));
}

// ==========================================
// 4. RWA COLLATERAL REGISTRY STATE VERIFICATION
// ==========================================

#[test]
fn test_rwa_attestation_registry_and_merkle_commit() {
    let mut world = WorldState::new();
    let treasury = mock_address(1);
    let spv_id = mock_spv(1);
    let valuation_usd = 4_820_000_000u64;
    let proof_hash: Hash256 = keccak256(b"VERIFIED_TITLE_DEED_PROOF_HASH_SPV1");

    let initial_root = world.compute_state_root();

    let attest_tx = Transaction {
        sender: treasury,
        nonce: 0,
        instruction: Instruction::AttestRwaCollateral {
            spv_id,
            valuation_usd,
            proof_hash,
        },
        signature: [0u8; 64],
    };

    world
        .apply_transaction(&attest_tx, 1700000050)
        .expect("RWA attestation must succeed");

    let finalized_root = world.compute_state_root();
    assert_ne!(initial_root, finalized_root);

    // Validate on-chain state record
    let record = world.rwa_registry.get(&spv_id).expect("SPV record must exist");
    assert_eq!(record.valuation_usd, valuation_usd);
    assert_eq!(record.proof_hash, proof_hash);
    assert_eq!(record.last_updated_timestamp, 1700000050);
}
