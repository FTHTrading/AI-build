import json
import time
import hashlib
import hmac
from typing import Dict, Any, List, Optional

class SovereignAssetOracle:
    """
    Institutional Proof-of-Reserves Oracle and Multi-Asset Attestation Engine.
    Emits cryptographically signed attestation envelopes with Merkle audit chains.
    """
    def __init__(self, enterprise_id: str = "69a0b54edd793f289161ec0c50cee070"):
        self.enterprise_id = enterprise_id
        self.oracle_signing_key = "unykorn_sovereign_oracle_secp256k1_key_v2"
        self.audit_history: List[Dict[str, Any]] = []
        
        # Asset registry tracking on-chain vs custody invariants
        self.asset_registry = {
            "dignity-gold": {
                "asset_name": "Dignity Gold Securitized Reserve",
                "symbol": "DIGau",
                "asset_class": "PHYSICAL_COMMODITY_GOLD",
                "vault_depository_ref": "BITGO-GOLD-VAULT-DIGAU-01",
                "contract_address": "0x3643000000000000000000000000000000000002",
                "onchain_total_supply": 10000000,
                "custody_units_allocated": 10000.0,
                "certified_reserve_ceiling": 25000.0,
                "unit_of_measure": "TROY_OUNCES",
                "assay_bar_serials": [
                    "BAR-AU-2026-9901-A", "BAR-AU-2026-9902-A", 
                    "BAR-AU-2026-9903-A", "BAR-AU-2026-9904-A"
                ],
                "compliance_rules": [
                    {
                        "rule_id": "ONCHAINID_10101_KYC",
                        "enforced": True,
                        "description": "Standardized Identity Registry KYC Claim",
                        "claim_topic": 10101
                    },
                    {
                        "rule_id": "ONCHAINID_10102_AML",
                        "enforced": True,
                        "description": "Automated Sanctions and AML Clearance",
                        "claim_topic": 10102
                    },
                    {
                        "rule_id": "REG_D_LOCKUP",
                        "enforced": True,
                        "description": "US Accredited Investor Lockup Schedule",
                        "parameters": {
                            "lockup_duration_seconds": 31536000,
                            "exemption": "SEC Rule 144"
                        }
                    },
                    {
                        "rule_id": "SANCTION_FILTER",
                        "enforced": True,
                        "description": "ISO-3166 Sanctioned Country Guardrail",
                        "parameters": {
                            "blocked_country_codes": [408, 364]
                        }
                    }
                ]
            },
            "spv-clean-energy": {
                "asset_name": "SPV Clean Energy Solar-Plus-Storage Senior Tranche",
                "symbol": "RWA-SPV1",
                "asset_class": "STRUCTURED_PRIVATE_CREDIT",
                "vault_depository_ref": "CHARTER-BANK-ESCROW-44029102",
                "contract_address": "0x3643000000000000000000000000000000000001",
                "onchain_total_supply": 25000000,
                "custody_units_allocated": 25000000.00,
                "certified_reserve_ceiling": 50000000.00,
                "unit_of_measure": "USD_FIAT_ESCROW",
                "assay_bar_serials": [
                    "WIRE-FED-2026-08-A1", "WIRE-FED-2026-08-A2"
                ],
                "compliance_rules": [
                    {
                        "rule_id": "ONCHAINID_10101_KYC",
                        "enforced": True,
                        "claim_topic": 10101
                    },
                    {
                        "rule_id": "QUALIFIED_INSTITUTIONAL_BUYER",
                        "enforced": True,
                        "claim_topic": 10103,
                        "parameters": {
                            "min_investment_usd": 1000000.00
                        }
                    }
                ]
            }
        }

    def _compute_merkle_root(self, leaves: List[str]) -> str:
        if not leaves:
            return "0x" + "0" * 64
        tree = [hashlib.sha256(leaf.encode()).hexdigest() for leaf in leaves]
        while len(tree) > 1:
            if len(tree) % 2 != 0:
                tree.append(tree[-1])
            tree = [hashlib.sha256((tree[i] + tree[i+1]).encode()).hexdigest() for i in range(0, len(tree), 2)]
        return "0x" + tree[0]

    def generate_attestation_envelope(self, asset_key: str) -> Dict[str, Any]:
        asset = self.asset_registry.get(asset_key.lower())
        if not asset:
            raise KeyError(f"Asset '{asset_key}' not registered in Sovereign Oracle.")

        merkle_root = self._compute_merkle_root(asset["assay_bar_serials"])
        timestamp = int(time.time())
        
        # Calculate backing ratio
        backing_ratio = 1.0
        if asset["onchain_total_supply"] > 0:
            if asset["unit_of_measure"] == "TROY_OUNCES":
                backing_ratio = (asset["custody_units_allocated"] * 1000) / asset["onchain_total_supply"]
            else:
                backing_ratio = asset["custody_units_allocated"] / asset["onchain_total_supply"]

        # Core attestation payload
        payload = {
            "oracle_version": "2.1.0-sovereign",
            "enterprise_id": self.enterprise_id,
            "asset_key": asset_key,
            "asset_name": asset["asset_name"],
            "symbol": asset["symbol"],
            "asset_class": asset["asset_class"],
            "contract_address": asset["contract_address"],
            "vault_depository_ref": asset["vault_depository_ref"],
            "timestamp": timestamp,
            "metrics": {
                "onchain_total_supply": asset["onchain_total_supply"],
                "custody_units_allocated": asset["custody_units_allocated"],
                "certified_reserve_ceiling": asset["certified_reserve_ceiling"],
                "unit_of_measure": asset["unit_of_measure"],
                "reserve_backing_ratio": f"{backing_ratio:.2f}x",
                "invariant_status": "VALID_COLLATERALIZED" if backing_ratio >= 1.0 else "DEFICIT_HALT"
            },
            "assay_merkle_root": merkle_root,
            "compliance_rules": asset["compliance_rules"]
        }

        # Deterministic Payload Hash & Signature Envelope
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload_hash = "0x" + hashlib.sha256(payload_bytes).hexdigest()
        signature = "0x" + hmac.new(self.oracle_signing_key.encode(), payload_bytes, hashlib.sha256).hexdigest()

        envelope = {
            "signature_envelope": {
                "signature": signature,
                "payload_hash": payload_hash,
                "signer_identity": f"did:unykorn:oracle:{self.enterprise_id[:8]}",
                "algorithm": "HMAC-SHA256-ORACLE-V2",
                "signed_at": timestamp
            },
            "attestation": payload
        }

        # Record in historical audit chain
        self.audit_history.append({
            "attestation_index": len(self.audit_history) + 1,
            "timestamp": timestamp,
            "asset_key": asset_key,
            "payload_hash": payload_hash,
            "merkle_root": merkle_root
        })

        return envelope

    def get_audit_history(self, asset_key: Optional[str] = None) -> List[Dict[str, Any]]:
        if asset_key:
            return [a for a in self.audit_history if a["asset_key"].lower() == asset_key.lower()]
        return self.audit_history
