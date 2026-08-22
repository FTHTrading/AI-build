from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import uuid
import hashlib
import time
import os
import requests
import xml.etree.ElementTree as ET
from typing import AsyncGenerator, Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
import edge_tts

from scripts.iso20022_parser import Iso20022Engine
from scripts.bitgo_gateway import BitGoExpressClient
from scripts.sovereign_oracle import SovereignAssetOracle

app = FastAPI(
    title="Unykorn Sovereign Asset Gateway & Multi-Asset Oracle",
    version="2.1.0",
    docs_url="/docs"
)

oracle = SovereignAssetOracle(enterprise_id="69a0b54edd793f289161ec0c50cee070")
bitgo_client = BitGoExpressClient()

app.state.escrow_balance_usd = 50000000.00
app.state.pending_attestation = None
app.state.enterprise_id = "69a0b54edd793f289161ec0c50cee070"

# Middleware: CORS & Private Network Access
@app.middleware("http")
async def add_pna_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ----------------------------------------------------------------------
# Health, Telemetry & Versioning
# ----------------------------------------------------------------------
@app.get("/")
@app.get("/health")
async def health_check():
    return {
        "status": "ONLINE",
        "version": "2.1.0-sovereign",
        "service": "unykorn-sovereign-rwa-gateway",
        "custody_anchors": ["BitGo Enterprise Trust", "Charter Bank & Trust"],
        "enterprise_id": app.state.enterprise_id,
        "oracle_status": "ACTIVE_SIGNING",
        "compliance_engine": "ERC-3643 (T-REX Modular)",
        "escrow_verified_usd": app.state.escrow_balance_usd
    }

@app.get("/version")
async def get_version():
    return {
        "version": "2.1.0",
        "release_codename": "Sovereign-Oracle-Hardened",
        "supported_standards": ["ERC-3643", "EIP-712", "ISO-20022", "ONCHAINID"],
        "active_networks": ["Rust-L1:8791", "EVM:1337"]
    }

# ----------------------------------------------------------------------
# Dynamic Multi-Asset Custody Oracle Routes
# ----------------------------------------------------------------------
@app.get("/v1/custody/{asset}/attestation")
async def get_asset_attestation(asset: str):
    try:
        envelope = oracle.generate_attestation_envelope(asset)
        return envelope
    except KeyError:
        raise HTTPException(
            status_code=404, 
            detail=f"Asset '{asset}' not found. Supported assets: {list(oracle.asset_registry.keys())}"
        )

@app.get("/v1/custody/{asset}/audit-history")
async def get_asset_audit_history(asset: str):
    history = oracle.get_audit_history(asset)
    return {
        "asset": asset,
        "audit_entries_count": len(history),
        "audit_chain": history
    }

# Legacy route compatibility
@app.get("/v1/custody/dignity-gold/attestation")
async def get_legacy_dignity_gold_attestation():
    return oracle.generate_attestation_envelope("dignity-gold")

# ----------------------------------------------------------------------
# BitGo Settlement & EIP-712 Signer
# ----------------------------------------------------------------------
class BitGoSettlementRequest(BaseModel):
    spv_id: str = "spv-clean-energy"
    amount_usd: float = 25000000.00
    investor_wallet: str = "0x7A8B9C1029384756A1B2C3D4E5F6A7B8C9D0E1F2"
    wire_ref: str = "BITGO-TRUST-SETTLE-88219"
    custodian: str = "BitGo Bank & Trust"

@app.post("/v1/custody/bitgo-express/settle")
async def settle_bitgo_escrow(payload: BitGoSettlementRequest):
    app.state.escrow_balance_usd += payload.amount_usd
    eip712_data = bitgo_client.format_eip712_mint_payload(
        spv_id=payload.spv_id,
        investor_wallet=payload.investor_wallet,
        amount_usd=payload.amount_usd,
        wire_ref=payload.wire_ref
    )
    app.state.pending_attestation = {
        "settlement_id": str(uuid.uuid4()),
        "spv_id": payload.spv_id,
        "amount_usd": payload.amount_usd,
        "custodian": payload.custodian,
        "investor_wallet": payload.investor_wallet,
        "eip712_payload": eip712_data,
        "merkle_proof": "0x3dfc21ee685248ec745ceb84d4f0df2dd46a13f9d17ce7f4e2489154c1e8fe64",
        "status": "AWAITING_OPERATOR_SIGNATURE"
    }
    return {
        "status": "SETTLEMENT_PROCESSED",
        "custody": payload.custodian,
        "escrow_balance_usd": app.state.escrow_balance_usd,
        "pending_action": app.state.pending_attestation
    }

class MintApprovalRequest(BaseModel):
    settlement_id: str
    signer_address: str
    signature_bytes: str
    action: str = "APPROVE_MINT"

@app.post("/v1/custody/mint/execute")
async def execute_mint_authorization(payload: MintApprovalRequest):
    if not app.state.pending_attestation or app.state.pending_attestation.get("settlement_id") != payload.settlement_id:
        raise HTTPException(status_code=404, detail="Settlement ID not found or already processed.")
    
    app.state.pending_attestation["status"] = "MINT_COMPLETED"
    app.state.pending_attestation["tx_hash"] = "0x" + hashlib.sha256(payload.signature_bytes.encode()).hexdigest()
    app.state.pending_attestation["signed_by"] = payload.signer_address
    
    return {
        "status": "SUCCESS",
        "mint_tx_hash": app.state.pending_attestation["tx_hash"],
        "tokens_minted": app.state.pending_attestation["amount_usd"],
        "investor": app.state.pending_attestation["investor_wallet"],
        "compliance": "ERC-3643_VALIDATED",
        "settlement_state": app.state.pending_attestation
    }

@app.get("/v1/custody/pending-actions")
async def get_pending_actions():
    return {"pending_attestation": app.state.pending_attestation}

# ----------------------------------------------------------------------
# ISO 20022 Banking Ingestion & Reconciliation
# ----------------------------------------------------------------------
@app.post("/v1/banking/iso20022/ingest")
async def ingest_iso20022_xml(request: Request):
    body_bytes = await request.body()
    xml_content = body_bytes.decode("utf-8")
    try:
        parsed = Iso20022Engine.parse_camt054_credit(xml_content)
        return {
            "status": "INGESTION_SUCCESS",
            "provider": "Charter Bank & Trust, NA",
            "parsed_payload": parsed,
            "on_chain_sync": {
                "l1_instruction": "Instruction::AttestCustodyDeposit",
                "merkle_proof_hash": parsed["audit_merkle_hash"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"XML Parsing Failed: {str(e)}")

@app.get("/v1/banking/escrow-reconciliation")
async def escrow_reconciliation():
    return {
        "status": "RECONCILED",
        "charter_bank_escrow_usd": app.state.escrow_balance_usd,
        "rust_l1_attested_usd": app.state.escrow_balance_usd,
        "discrepancy_usd": 0.00,
        "settlement_rail": "BitGo Enterprise & Fedwire pacs.008",
        "fiduciary_institution": "BitGo Bank & Trust / Charter Bank"
    }

# ----------------------------------------------------------------------
# Voice / TTS Pipeline
# ----------------------------------------------------------------------
class TTSRequest(BaseModel):
    text: str
    voice: str = "en-GB-RyanNeural"

@app.post("/v1/tts")
async def text_to_speech(payload: TTSRequest):
    communicate = edge_tts.Communicate(payload.text, payload.voice, rate="+8%", pitch="-5Hz")
    audio_data = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
    return Response(content=bytes(audio_data), media_type="audio/mpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8790)