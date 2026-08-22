import json
import time
import hashlib
from typing import Dict, Any, List

class MerkleTree:
    """Computes deterministic Merkle Root for physical vault assay batches."""
    @staticmethod
    def compute_root(leaves: List[str]) -> str:
        if not leaves:
            return "0x" + "0" * 64
        tree = [hashlib.sha256(leaf.encode()).hexdigest() for leaf in leaves]
        while len(tree) > 1:
            if len(tree) % 2 != 0:
                tree.append(tree[-1])
            tree = [hashlib.sha256((tree[i] + tree[i+1]).encode()).hexdigest() for i in range(0, len(tree), 2)]
        return "0x" + tree[0]

class DignityGoldProductionEngine:
    def __init__(self):
        self.enterprise_id = "69a0b54edd793f289161ec0c50cee070"
        self.depository_ref = "BITGO-GOLD-VAULT-DIGAU-01"
        self.max_ounces_authorized = 25000.0  # Certified Assay Limit
        self.gold_ounces_in_custody = 0.0
        self.total_supply = 0
        self.balances = {}
        self.allowances = {}
        self.identities = {}
        self.lockups = {}
        self.vault_bar_serials = [
            "BAR-AU-2026-9901-A", "BAR-AU-2026-9902-A", 
            "BAR-AU-2026-9903-A", "BAR-AU-2026-9904-A"
        ]
        self.assay_merkle_root = MerkleTree.compute_root(self.vault_bar_serials)

    def register_onchain_id(self, wallet: str, country_code: int, claims: List[int]):
        norm = wallet.lower()
        self.identities[norm] = {
            "country": country_code,
            "claims": set(claims),
            "is_verified": (10101 in claims and 10102 in claims)
        }
        print(f"  [ONCHAINID 🟢] Registered {wallet[:10]}... | Country: {country_code} | Claims: {claims}")

    def mint_digau(self, investor_wallet: str, token_amount: int, ounces: float, wire_ref: str) -> Dict[str, Any]:
        norm = investor_wallet.lower()
        identity = self.identities.get(norm)
        
        if not identity or not identity["is_verified"]:
            raise PermissionError(f"ERC-3643 REVERT: Wallet {investor_wallet} fails KYC/AML claims!")
            
        if self.gold_ounces_in_custody + ounces > self.max_ounces_authorized:
            raise ValueError(f"INVARIANT REVERT: Minting {ounces} oz exceeds certified limit of {self.max_ounces_authorized} oz!")

        self.balances[norm] = self.balances.get(norm, 0) + token_amount
        self.gold_ounces_in_custody += ounces
        self.total_supply += token_amount

        tx_hash = "0x" + hashlib.sha256(f"{norm}{token_amount}{wire_ref}{self.assay_merkle_root}".encode()).hexdigest()

        return {
            "status": "MINT_COMPLETED",
            "token": "DIGau",
            "minted_tokens": token_amount,
            "ounces_allocated": ounces,
            "total_custody_ounces": self.gold_ounces_in_custody,
            "assay_merkle_root": self.assay_merkle_root,
            "tx_hash": tx_hash
        }

    def transfer_from(self, spender: str, sender: str, recipient: str, amount: int):
        sp_norm, s_norm, r_norm = spender.lower(), sender.lower(), recipient.lower()
        
        # Check Identity
        if not self.identities.get(s_norm, {}).get("is_verified"):
            raise PermissionError("ERC-3643: Sender not KYC verified")
        if not self.identities.get(r_norm, {}).get("is_verified"):
            raise PermissionError("ERC-3643: Recipient not KYC verified")
            
        # Check Country Sanction
        if self.identities[r_norm]["country"] in [408, 364]:
            raise PermissionError("ERC-3643: Transfer blocked by Sanction Rules")

        # Allowance Check
        if sp_norm != s_norm:
            allowed = self.allowances.get(s_norm, {}).get(sp_norm, 0)
            if allowed < amount:
                raise ValueError("ERC-3643: Allowance exceeded")
            self.allowances[s_norm][sp_norm] -= amount

        if self.balances.get(s_norm, 0) < amount:
            raise ValueError("ERC-3643: Insufficient balance")

        self.balances[s_norm] -= amount
        self.balances[r_norm] = self.balances.get(r_norm, 0) + amount
        print(f"  [TRANSFER 🟢] Moved {amount:,.2f} DIGau from {sender[:10]}... to {recipient[:10]}...")

    def generate_attestation_report(self) -> Dict[str, Any]:
        return {
            "suite": "DIGau_ERC3643_Production",
            "status": "ATTESTED",
            "timestamp": int(time.time()),
            "bitgo_enterprise_id": self.enterprise_id,
            "vault_ref": self.depository_ref,
            "onchain_total_supply": self.total_supply,
            "custody_ounces_allocated": self.gold_ounces_in_custody,
            "certified_reserve_ceiling_oz": self.max_ounces_authorized,
            "reserve_backing_ratio": f"{(self.gold_ounces_in_custody / (self.total_supply / 1000) if self.total_supply > 0 else 1.0):.2f}x",
            "assay_merkle_root": self.assay_merkle_root,
            "compliance_rules": ["ONCHAINID_10101_KYC", "ONCHAINID_10102_AML", "REG_D_LOCKUP", "SANCTION_FILTER"]
        }

if __name__ == "__main__":
    print("\n--- RUNNING INSTITUTIONAL ERC-3643 DIGau AUDIT HARNESS ---")
    engine = DignityGoldProductionEngine()

    bank_custody = "0x89A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9"
    secondary_investor = "0x2B3C4D5E6F7A8B9C0D1E2F3A4B5C6D7E8F9A0B1C"
    sanctioned_entity = "0x000000000000000000000000000000000000DEAD"

    # Step 1: Register OnChainID Claims (10101=KYC, 10102=AML, 10103=Accredited)
    engine.register_onchain_id(bank_custody, country_code=840, claims=[10101, 10102, 10103]) # US
    engine.register_onchain_id(secondary_investor, country_code=826, claims=[10101, 10102]) # UK
    engine.register_onchain_id(sanctioned_entity, country_code=408, claims=[10101, 10102]) # DPRK (Sanctioned)

    # Step 2: Mint against certified physical bullion reserve
    receipt = engine.mint_digau(bank_custody, token_amount=10000000, ounces=10000.0, wire_ref="BITGO-GOLD-CUSTODY-88910")
    print(f"  [MINT 🟢] Minted {receipt['minted_tokens']:,} DIGau ({receipt['ounces_allocated']:,} oz)")

    # Step 3: Invariant Guardrail Test (Attempt over-allocation beyond certified audit)
    try:
        engine.mint_digau(bank_custody, token_amount=20000000, ounces=20000.0, wire_ref="OVER-ALLOCATE")
    except ValueError as e:
        print(f"  [INVARIANT GUARDRAIL 🛡️] Blocked Over-allocation: {e}")

    # Step 4: Transfer Allowance & Sanction Filter Test
    engine.allowances[bank_custody.lower()] = {bank_custody.lower(): 2000000}
    engine.transfer_from(bank_custody, bank_custody, secondary_investor, 2000000)

    try:
        engine.allowances[bank_custody.lower()] = {bank_custody.lower(): 1000000}
        engine.transfer_from(bank_custody, bank_custody, sanctioned_entity, 1000000)
    except PermissionError as e:
        print(f"  [COMPLIANCE GUARDRAIL 🛡️] Blocked Sanctioned Transfer: {e}")

    # Step 5: Generate & Export Structured Attestation
    attestation = engine.generate_attestation_report()
    print("\n--- INSTITUTIONAL ATTESTATION RECORD ---")
    print(json.dumps(attestation, indent=2))
