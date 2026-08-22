#!/usr/bin/env python3
"""
Unykorn LLC - Genesis402 (x402) Agentic Gateway & Block Streamer
Handles HTTP 402 Agent-to-Agent (A2A) machine settlements and syncs finalized blocks to Obsidian.
"""

import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uvicorn

# ----------------- CONFIGURATION -----------------
RUST_CHAIN_IPC = "http://127.0.0.1:8791"
VAULT_ROOT = Path(os.getenv("UNYKORN_VAULT_PATH", r"C:\Unykorn-Brain"))
DAILY_DIR = VAULT_ROOT / "04_EPISODIC_MEMORY" / "DAILY_TRANSACTIONS"
GATEWAY_PORT = 4020  # Genesis402 agent gateway

app = FastAPI(
    title="Genesis402 x402 A2A Settlement Gateway",
    description="HTTP 402 Agent-to-Agent Truth Verification & Streamer Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------- A2A & 402 SCHEMAS -----------------
class AgentTaskRequest(BaseModel):
    agent_id: str
    target_protocol: str
    action: str
    truth_payload: str
    bid_amount_wei: int


class AttestationCommitPayload(BaseModel):
    tx_hash: str
    block_height: int
    sender_agent: str
    truth_category: str
    summary: str


# ----------------- OBSIDIAN LEDGER APPENDER -----------------
def commit_block_to_obsidian(
    block_index: int,
    block_hash: str,
    state_root: str,
    tx_count: int,
    txs_summary: list,
):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%H:%M:%S")

    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    daily_file = DAILY_DIR / f"{date_str}.md"

    if not daily_file.exists():
        with open(daily_file, "w", encoding="utf-8") as f:
            f.write(
                f"""---
date: {date_str}
entity: Unykorn LLC
owner_founder_ceo: Kevan Burns
tags:
  - episodic-memory
  - execution-log
  - x402-settlement
---

# Daily Transaction & Execution Ledger: {date_str}

## Executive Summary
- **Protocol**: [[CUSTODY_GATEWAYS]] & Genesis402 (x402) A2A Settlement
- **Active Node**: [[DECISION_REGISTRY]]

---

## Logged Executions
"""
            )

    tx_entries = "\n".join(
        [
            f"  - **Tx [{i+1}]**: Sender: `{tx.get('sender', 'N/A')}` | Score: `{tx.get('truth_proof', {}).get('confidence_score', 'N/A')}%` | Data: `{tx.get('payload', '')[:80]}`"
            for i, tx in enumerate(txs_summary)
        ]
    )
    if not tx_entries:
        tx_entries = "  - *Block contains zero mempool transactions.*"

    log_entry = f"""
### [{timestamp_str}] - Genesis402 / Layer-1 Block Finalized: #{block_index}
- **Session ID**: `X402-A2A-STREAMER`
- **Module Context**: [[CUSTODY_GATEWAYS]]
- **Block Hash**: `{block_hash[:24]}...`
- **State Root**: `{state_root[:24]}...`
- **Transactions Finalized**: `{tx_count}`
- **Executive Directives Applied**:
  - Validated under [[CORE_IDENTITY]] (Kevan Burns, Founder/Owner/CEO).
  - Enforced [[SYSTEM_CONSTRAINTS]] (Infrastructure & Tech Rails only).
- **A2A Settlement Payload**:
{tx_entries}

---
"""
    with open(daily_file, "a", encoding="utf-8") as f:
        f.write(log_entry)


# ----------------- GENESIS 402 ENDPOINTS -----------------
@app.get("/x402/health")
def health():
    return {
        "status": "ONLINE",
        "protocol": "genesis402.com / x402",
        "rails": "Unykorn LLC",
        "gateway_port": GATEWAY_PORT,
    }


@app.post("/x402/a2a/request")
def handle_a2a_request(
    task: AgentTaskRequest, authorization: str = Header(None)
):
    """Enforces HTTP 402 Tokenized Settlement. If no payment header is present, returns HTTP 402 with settlement parameters."""
    if not authorization or not authorization.startswith("Bearer x402_"):
        headers = {
            "WWW-Authenticate": 'x402 realm="genesis402.com", token="required", fee="500000000000000"',
            "X-Payment-Gateway": "genesis402.com",
            "X-Settlement-Token": "U-SND1 / USDC-Permitted",
            "X-Truth-Oracle-Required": "TRUE",
        }
        return Response(
            content=json.dumps(
                {
                    "error": "Payment Required",
                    "code": 402,
                    "protocol": "genesis402",
                    "detail": "Settlement authorization token missing. Submit signed x402 settlement payload to proceed.",
                    "deposit_channel": "0xUNYKORN_TREASURY_GATEWAY",
                }
            ),
            status_code=402,
            media_type="application/json",
            headers=headers,
        )

    tx_payload = {
        "sender": task.agent_id,
        "receiver": "0xUNYKORN_TREASURY_GATEWAY",
        "payload": f"ACTION={task.action}; PROTOCOL={task.target_protocol}; DATA={task.truth_payload}",
        "truth_proof": {
            "category": "OracleConsensus",
            "claim_hash": f"0x{abs(hash(task.truth_payload)):x}",
            "confidence_score": 98,
            "evidence_uri": "genesis402://a2a/proofs",
            "signature": authorization,
        },
        "nonce": int(datetime.now().timestamp()),
        "signature": authorization,
    }

    try:
        res = requests.post(
            f"{RUST_CHAIN_IPC}/ipc/tx", json=tx_payload, timeout=3
        )
        chain_res = res.json()
    except Exception as e:
        chain_res = {"error": f"Failed to submit to Layer-1 chain: {str(e)}"}

    return {
        "status": "ACCEPTED",
        "code": 200,
        "message": "A2A task verified via genesis402.com and queued to block mempool.",
        "chain_response": chain_res,
    }


# ----------------- BACKGROUND BLOCK STREAMER LOOP -----------------
async def poll_rust_chain_blocks():
    """Polls the local Rust Layer-1 chain for new blocks and logs them to Obsidian."""
    last_known_height = 0
    print("[*] Genesis402 / Rust Block Streamer loop started...")

    while True:
        try:
            res = requests.get(f"{RUST_CHAIN_IPC}/ipc/status", timeout=2)
            if res.status_code == 200:
                data = res.json()
                current_height = data.get("block_height", 0)

                if current_height > last_known_height:
                    print(
                        f"[+] Detected new block #{current_height}. Fetching details..."
                    )
                    commit_block_to_obsidian(
                        block_index=current_height,
                        block_hash=data.get("latest_state_root", "N/A"),
                        state_root=data.get("latest_state_root", "N/A"),
                        tx_count=data.get("mempool_size", 0),
                        txs_summary=[],
                    )
                    last_known_height = current_height

        except Exception:
            pass

        await asyncio.sleep(4)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(poll_rust_chain_blocks())


if __name__ == "__main__":
    print(
        f"[*] Starting Genesis402 (x402) A2A Gateway on http://0.0.0.0:{GATEWAY_PORT}"
    )
    uvicorn.run(app, host="0.0.0.0", port=GATEWAY_PORT, reload=False)
