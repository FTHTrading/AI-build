import os
import hmac
import hashlib
import time
import json
from typing import Dict, Any

class BitGoExpressClient:
    def __init__(self, base_url: str = "http://127.0.0.1:3080", access_token: str = None, webhook_secret: str = None):
        self.base_url = base_url
        self.access_token = access_token or os.getenv("BITGO_ACCESS_TOKEN", "v2x_unykorn_enterprise_sandbox_token")
        self.webhook_secret = webhook_secret or os.getenv("BITGO_WEBHOOK_SECRET", "whsec_unykorn_bitgo_hmac_secret")

    def verify_webhook_signature(self, raw_body: bytes, received_signature: str) -> bool:
        """Validates BitGo Express HMAC-SHA256 signature."""
        if not received_signature:
            return False
        expected_sig = hmac.new(
            self.webhook_secret.encode(),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_sig, received_signature)

    def format_eip712_mint_payload(self, spv_id: str, investor_wallet: str, amount_usd: float, wire_ref: str) -> Dict[str, Any]:
        """Builds strict EIP-712 structured data for ERC-3643 token minting."""
        token_units = int(amount_usd)
        return {
            "domain": {
                "name": "Unykorn RWA Compliance Engine",
                "version": "1.0.0",
                "chainId": 1337,
                "verifyingContract": "0x3643000000000000000000000000000000000001"
            },
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "MintSecuritizedTranche": [
                    {"name": "spvId", "type": "string"},
                    {"name": "investor", "type": "address"},
                    {"name": "tokenAmount", "type": "uint256"},
                    {"name": "bankWireRef", "type": "string"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "expiryBlock", "type": "uint256"}
                ]
            },
            "primaryType": "MintSecuritizedTranche",
            "message": {
                "spvId": spv_id,
                "investor": investor_wallet,
                "tokenAmount": token_units,
                "bankWireRef": wire_ref,
                "nonce": 1,
                "expiryBlock": 120
            }
        }
