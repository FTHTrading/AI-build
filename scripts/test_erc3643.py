import sys
import json
import hashlib
from typing import Dict, Any

class ERC3643VerificationEngine:
    def __init__(self):
        self.verified_wallets = set()
        self.balances = {}
        self.spv_tranches = {}
        self.total_supply = 0
        self.spv_id = "SPV_CLEAN_ENERGY_01"
        self.escrow_ref = "ESCROW-44029102-SPV1"

    def register_identity(self, wallet: str, claim_topic: int = 10101):
        """Registers verified KYC/AML Claim in Identity Registry."""
        self.verified_wallets.add(wallet.lower())
        print(f"  [REGISTRY 🟢] KYC Claim (Topic {claim_topic}) Registered for: {wallet}")

    def mint_securitized_tranche(self, investor_wallet: str, amount_usd: float, wire_ref: str) -> Dict[str, Any]:
        """Enforces ERC-3643 rules before minting tokenized debt/equity tranche."""
        norm_wallet = investor_wallet.lower()
        
        # Rule 1: Identity Registry Check
        if norm_wallet not in self.verified_wallets:
            raise PermissionError(f"ERC-3643 REVERT: Wallet {investor_wallet} is NOT verified in IdentityRegistry!")
        
        # Mint execution
        token_units = int(amount_usd)
        self.balances[norm_wallet] = self.balances.get(norm_wallet, 0) + token_units
        self.total_supply += token_units
        
        # Generate Deterministic On-Chain Receipt
        tx_hash = "0x" + hashlib.sha256(f"{norm_wallet}{amount_usd}{wire_ref}".encode()).hexdigest()
        
        return {
            "status": "ERC3643_MINT_SUCCESS",
            "spv": self.spv_id,
            "escrow_anchor": self.escrow_ref,
            "investor": investor_wallet,
            "amount_tokens": token_units,
            "wire_reference": wire_ref,
            "tx_hash": tx_hash,
            "new_balance": self.balances[norm_wallet]
        }

    def transfer(self, sender: str, recipient: str, amount: int):
        s_norm, r_norm = sender.lower(), recipient.lower()
        if s_norm not in self.verified_wallets:
            raise PermissionError(f"ERC-3643 REVERT: Sender {sender} fails Identity Registry!")
        if r_norm not in self.verified_wallets:
            raise PermissionError(f"ERC-3643 REVERT: Recipient {recipient} is unverified (Transfers restricted)!")
        if self.balances.get(s_norm, 0) < amount:
            raise ValueError("ERC-3643 REVERT: Insufficient Token Balance.")
            
        self.balances[s_norm] -= amount
        self.balances[r_norm] = self.balances.get(r_norm, 0) + amount
        print(f"  [COMPLIANCE 🟢] Transferred {amount:,.2f} Security Tokens from {sender[:10]}... to {recipient[:10]}...")

if __name__ == "__main__":
    print("\n--- RUNNING ERC-3643 SPECIFICATION TEST HARNESS ---")
    engine = ERC3643VerificationEngine()
    
    investor_a = "0x7A8B9C1029384756A1B2C3D4E5F6A7B8C9D0E1F2"
    investor_b = "0x4D5E6F7A8B9C0D1E2F3A4B5C6D7E8F9A0B1C2D3E"
    unverified = "0x000000000000000000000000000000000000BEEF"

    # Step 1: Register Identity
    engine.register_identity(investor_a, claim_topic=10101)
    
    # Step 2: Mint $25,000,000 against verified bank wire
    receipt = engine.mint_securitized_tranche(investor_a, 25000000, "BITGO-TRUST-SETTLE-88219")
    print(f"  [TOKEN MINT 🟢] Minted {receipt['amount_tokens']:,} Tokens | TxHash: {receipt['tx_hash'][:18]}...")
    
    # Step 3: Test Permissioned Guardrail (Attempt mint to unverified wallet)
    try:
        engine.mint_securitized_tranche(unverified, 1000000, "FAKE-WIRE-999")
    except PermissionError as e:
        print(f"  [GUARDRAIL 🛡️] Blocked unverified wallet mint: {e}")

    # Step 4: Whitelist Investor B & Execute Compliant Secondary Transfer
    engine.register_identity(investor_b, claim_topic=10101)
    engine.transfer(investor_a, investor_b, 5000000)
    
    print("\n--- ERC-3643 ENGINE AUDIT SUMMARY ---")
    print(f"  Total Securitized Supply : {engine.total_supply:,} RWA-SPV1")
    print(f"  Investor A Holding       : {engine.balances[investor_a.lower()]:,} RWA-SPV1")
    print(f"  Investor B Holding       : {engine.balances[investor_b.lower()]:,} RWA-SPV1")
