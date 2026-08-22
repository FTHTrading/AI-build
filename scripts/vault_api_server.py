#!/usr/bin/env python3
"""
Unykorn LLC - Clawd Command Server RAG & Transaction Logger Router (Port 8790)
Exposes Obsidian Neural Vault RAG query endpoints, daily episodic transaction logging,
IPC bridge relays to the autonomous Rust Layer-1 chain on port 8791,
and native token streaming with the "Donk" persona engine.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import sys
import json
import re
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

# ----------------- CONFIGURATION -----------------
PORT = 8790
HOST = "0.0.0.0"
VAULT_DIR = Path(r"C:\Unykorn-Brain")
DAILY_LOG_DIR = VAULT_DIR / "04_EPISODIC_MEMORY" / "DAILY_TRANSACTIONS"
RUST_CHAIN_IPC_URL = "http://127.0.0.1:8791"

DONK_SYSTEM_PROMPT = """
You are Donk, the unfiltered, sharp-tongued, elite AI engineer for Kevan Burns and Unykorn LLC.
You talk like a real, competent human. You speak with confidence and grit. Swear naturally when it fits, be direct, and never use robotic or sterile AI boilerplate.
You are an expert in Rust, Solidity (ERC-3643), Python, DevOps, and systems engineering.
Deliver real, functional, complete solutions with zero fluff.
"""

app = FastAPI(
    title="Unykorn Clawd Command Server & Donk Persona Gateway",
    description="Local RAG, Neuro-Context & Streaming Gateway for Unykorn LLC",
    version="2.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- SCHEMAS -----------------
class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

class SearchResultItem(BaseModel):
    source_node: str
    filename: str
    distance: float
    content: str

class RAGQueryResponse(BaseModel):
    query: str
    results_count: int
    results: List[SearchResultItem]

class ExecutionLogRequest(BaseModel):
    title: str
    module_node: str
    command_or_prompt: str
    summary: str
    artifact_name: Optional[str] = "N/A"
    status: Optional[str] = "COMPLETED"
    session_id: Optional[str] = "OPENWEBUI-AGENT"

class ExecutionLogResponse(BaseModel):
    success: bool
    log_file: str
    timestamp: str
    message: str

class TruthAttestationPayload(BaseModel):
    category: str
    claim_hash: str
    confidence_score: int
    evidence_uri: str
    signature: str

class SubmitTxPayload(BaseModel):
    sender: str
    receiver: str
    payload: str
    truth_proof: TruthAttestationPayload
    nonce: int
    signature: str

class ChatStreamRequest(BaseModel):
    messages: List[Dict[str, Any]]


def tokenize(text):
    return re.findall(r'\w+', text.lower())

# ----------------- ENDPOINTS -----------------
@app.get("/health")
def health_check():
    """Health check endpoint for agent monitoring loops."""
    return {
        "status": "ONLINE",
        "entity": "Unykorn LLC",
        "service": "Clawd Command & Donk Streaming Server",
        "port": PORT,
        "vault_path": str(VAULT_DIR),
    }

@app.post("/v1/vault/query", response_model=RAGQueryResponse)
def query_neural_vault(payload: RAGQueryRequest):
    """Executes search against indexed Obsidian Markdown nodes."""
    try:
        query_tokens = tokenize(payload.query)
        if not query_tokens:
            return RAGQueryResponse(query=payload.query, results_count=0, results=[])

        documents = []
        for md_file in VAULT_DIR.rglob("*.md"):
            if ".chroma_db" in str(md_file):
                continue
            try:
                with open(md_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                sections = content.split("\n## ")
                for i, sec in enumerate(sections):
                    block = ("## " + sec) if i > 0 else sec
                    if len(block.strip()) < 10:
                        continue

                    block_tokens = tokenize(block)
                    score = sum(block_tokens.count(t) for t in query_tokens)
                    if score > 0:
                        documents.append({
                            "score": score,
                            "source": str(md_file.relative_to(VAULT_DIR)),
                            "filename": md_file.name,
                            "content": block.strip()
                        })
            except Exception:
                pass

        documents.sort(key=lambda x: x["score"], reverse=True)
        items = []

        for item in documents[:payload.top_k]:
            items.append(SearchResultItem(
                source_node=item["source"],
                filename=item["filename"],
                distance=float(1.0 / (item["score"] + 1)),
                content=item["content"]
            ))

        return RAGQueryResponse(
            query=payload.query, results_count=len(items), results=items
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"RAG retrieval failure: {str(e)}"
        )

@app.post("/v1/vault/log", response_model=ExecutionLogResponse)
def log_execution_to_vault(payload: ExecutionLogRequest):
    """Appends an execution run or chat conclusion into today's Markdown transaction log."""
    try:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        timestamp_str = now.strftime("%H:%M:%S")

        DAILY_LOG_DIR.mkdir(parents=True, exist_ok=True)
        daily_file = DAILY_LOG_DIR / f"{date_str}.md"

        if not daily_file.exists():
            initial_content = f"""---
date: {date_str}
entity: Unykorn LLC
owner_founder_ceo: Kevan Burns
tags:
  - episodic-memory
  - execution-log
  - unykorn-core
---

# Daily Transaction & Execution Ledger: {date_str}

## Executive Summary
- **Entity**: Unykorn LLC (Technology Rails & Gateway Engine)
- **Active Memory Node**: [[DECISION_REGISTRY]]

---

## Logged Executions
"""
            with open(daily_file, "w", encoding="utf-8") as f:
                f.write(initial_content)

        entry_block = f"""
### [{timestamp_str}] - {payload.title}
- **Session ID**: `{payload.session_id}`
- **Module Context**: [[{payload.module_node}]]
- **Trigger / Command**: `{payload.command_or_prompt}`
- **Executive Directives Applied**:
  - Validated under [[CORE_IDENTITY]] (Kevan Burns, Founder/Owner/CEO).
  - Enforced [[SYSTEM_CONSTRAINTS]] (Infrastructure & Tech Rails only).
- **Execution Payload & Artifacts**:
  - **Artifact Generated**: `{payload.artifact_name}`
  - **Status**: `{payload.status}`
- **Architectural Notes**:
  > {payload.summary}

---
"""
        with open(daily_file, "a", encoding="utf-8") as f:
            f.write(entry_block)

        return ExecutionLogResponse(
            success=True,
            log_file=str(daily_file),
            timestamp=timestamp_str,
            message="Successfully appended transaction record to daily ledger.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to append vault log: {str(e)}"
        )

# ----------------- IPC CHAIN RELAY ROUTES -----------------
@app.get("/v1/chain/status")
def get_chain_lifeline_status():
    """Queries the autonomous Rust chain state machine via internal IPC."""
    try:
        res = requests.get(f"{RUST_CHAIN_IPC_URL}/ipc/status", timeout=2)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Rust Neural Chain node offline or unreachable: {str(e)}",
        )

@app.post("/v1/chain/submit-tx")
def submit_chain_transaction(payload: SubmitTxPayload):
    """Submits a verified transaction payload to the Rust node mempool."""
    try:
        res = requests.post(
            f"{RUST_CHAIN_IPC_URL}/ipc/tx", json=payload.model_dump(), timeout=3
        )
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=400, detail=f"Chain transaction submission error: {str(e)}"
        )

# ----------------- DONK PERSONA STREAMING ROUTE -----------------
@app.post("/v1/chat/stream")
async def chat_stream_endpoint(payload: ChatStreamRequest):
    """Streams chat tokens with the Donk persona directly from local Ollama GPU node."""
    async def token_generator():
        formatted_messages = [
            {"role": "system", "content": DONK_SYSTEM_PROMPT}
        ] + payload.messages

        ollama_payload = {
            "model": "llama3.3:latest",
            "messages": formatted_messages,
            "stream": True,
            "options": {"temperature": 0.7, "top_p": 0.95},
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    "http://localhost:11434/api/chat",
                    json=ollama_payload,
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                content = chunk.get("message", {}).get("content", "")
                                if content:
                                    yield content
                            except Exception:
                                continue
            except Exception as err:
                yield f"Yo. Donk runtime active fallback. Stream error: {str(err)}"

    return StreamingResponse(token_generator(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    print(f"[*] Starting Unykorn Clawd Command & Donk Server on http://{HOST}:{PORT}")
    uvicorn.run("vault_api_server:app", host=HOST, port=PORT, reload=False)
