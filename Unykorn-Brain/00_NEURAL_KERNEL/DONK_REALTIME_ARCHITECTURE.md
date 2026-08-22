# ⚡ DONK REALTIME AI ARCHITECTURE & ENTERPRISE INTERACTION LOOP
**Entity**: Unykorn LLC  
**Operator / Executive**: Kevan Burns (Founder, Owner & CEO)  
**Specification Version**: `v1.1.0-PROD`  
**System Architecture**: Policy-Governed Realtime Orchestrated AI Control-Room Runtime  

---

## 1. Executive Summary & Core Philosophy

Donk is a **Policy-Governed Autonomous Runtime** engineered to bridge natural language execution directly to the **Unykorn Layer-1 Rust State Machine**, the **ERC-3643 Permissioned Tokenization Suite**, and the **2,461-node Obsidian Neural Vault**.

Unlike generic chatbot wrappers, Donk functions as a deterministic **orchestrator and action engine** built upon streaming token delivery, persistent multi-tier memory, hybrid RAG retrieval, typed tool execution gates, and real-time WebRTC/WebSocket voice interaction loops.

---

## 2. Trust Boundaries & Security Architecture

```
 ┌──────────────┐     ┌──────────────┐     ┌───────────────────────────┐
 │  Browser /   ├────>│ API Gateway  ├────>│ Identity & Policy         │
 │  Control UI  │     │  (Port 8790) │     │ Decision Point (PDP)      │
 └──────────────┘     └──────────────┘     └─────────────┬─────────────┘
                                                         │
                                                         ▼
 ┌──────────────┐     ┌──────────────┐     ┌───────────────────────────┐
 │ Read / Draft │<────┤ Model Router │<────┤ Orchestration Engine      │
 │ Tool Workers │     │ (Local/CUDA) │     │ (State Machine Loop)      │
 └──────┬───────┘     └──────────────┘     └─────────────┬─────────────┘
        │                                                │
        ▼                                                ▼
 ┌──────────────┐                          ┌───────────────────────────┐
 │ Immutable RAG│                          │ EIP-712 External Wallet   │
 │ Evidence Vault                          │ Approval & Signer Service │
 └──────────────┘                          └───────────────────────────┘
```

### Critical Security Directives:
1. **Policy-Governed Labeling**: Replaces "Unrestricted Model" with **Policy-Governed Autonomous Runtime** across all interfaces.
2. **Zero Private-Key Exposure**: Model and orchestrator never hold private keys or production credentials.
3. **Anti-Prompt-Injection Boundary**: Retrieved RAG documents, tool logs, and web content are treated strictly as untrusted data payloads, never system instructions.
4. **Policy Decision Point (PDP)**: Evaluates user identity, workspace, environment, target allowlists, and spending limits prior to dispatching any tool worker.

---

## 3. The 7-Layer Enterprise Interaction System

| Layer | Functional Capability | Unykorn Engine Implementation |
| :--- | :--- | :--- |
| **1. Persona** | Stable voice, priorities, boundaries, and domain vocabulary | Versioned **Donk Constitution** (`DONK_PERSONA.md`): Direct, capable, policy-governed architect. |
| **2. Conversation Context** | Continuity, pronoun resolution, and prior decisions | Thread-local persistence with rolling summarization (500–1,500 token budgeted window). |
| **3. Long-Term Memory** | Durable preferences, project choices, and corrections | Structured **Memory Ledger** with explicit provenance, confidence scores, TTLs, and deletion controls. |
| **4. Retrieval (RAG)** | Grounded evidence from project docs and codebase | Hybrid lexical/vector search over the 2,461-node Obsidian corpus with confidence scores & citations. |
| **5. Tool Execution** | Safe on-chain actions, repository edits, and system jobs | Schema-validated, permissioned tool calls categorized into **Read, Draft, Write, and Irreversible** tiers. |
| **6. Realtime Streaming** | Zero-latency, natural output delivery | Server-Sent Events (SSE) / WebSockets transmitting status chips, text deltas, tool traces, and citations. |
| **7. Voice & Presence** | Natural, interruptible voice interaction | Persistent WebRTC audio sessions with Voice Activity Detection (VAD), barge-in support, and state sync. |

---

## 4. Approval Object Schema

All **Write** and **Irreversible** tool calls pause execution and emit a pending `Approval Object` to the user interface:

```json
{
  "approval_id": "apr_01k892bcde0981247aef",
  "run_id": "run_01k892bcde0981247aef",
  "actor_id": "kevan_burns_ceo",
  "workspace_id": "unykorn-core",
  "environment": "staging",
  "action": "chain_submit_tx",
  "risk": "irreversible",
  "intent": "Attest $4.82B USD SPV-1 collateral on Rust L1 state engine",
  "payload_hash": "sha256:892bcde0981247aefbcde0981247aefbcde0981247aefbcde0981247aefbcde0",
  "chain_id": 1,
  "contract": "0xUNYKORN_TREASURY_GATEWAY",
  "value": "4820000000",
  "nonce": "0",
  "expires_at": "2026-08-22T18:00:00Z",
  "status": "awaiting_signature"
}
```

---

## 5. Event Stream Envelope Contract

All real-time communications stream using a standardized event envelope:

```json
{
  "event_id": "evt_01k892bcde",
  "run_id": "run_01k892bcde",
  "thread_id": "thr_01k892bcde",
  "sequence": 42,
  "timestamp": "2026-08-22T11:27:00Z",
  "type": "tool.pending_approval",
  "data": {
    "tool": "chain_submit_tx",
    "risk": "irreversible",
    "approval_id": "apr_01k892bcde"
  }
}
```

---

## 6. Persisted Entity Data Model

| Entity | Primary Purpose | Storage Engine |
| :--- | :--- | :--- |
| **`threads` & `messages`** | Conversation history, user prompts, assistant replies, and rolling summaries | PostgreSQL / SQLite |
| **`memories`** | Transparent memory ledger (Session, User, Project, Operational) with TTLs | PostgreSQL + Redis |
| **`retrieval_chunks`** | Vector/lexical RAG chunks, source URIs, authority scores | ChromaDB / FAISS |
| **`runs` & `tool_calls`** | Orchestration execution traces, tool inputs/outputs, logs, and timing | PostgreSQL |
| **`approvals`** | Lifecycle state of pending and signed EIP-712 approvals | PostgreSQL |
| **`policies`** | Versioned security policies, target allowlists, and role permissions | YAML / PostgreSQL |
| **`events`** | Append-only audit stream of all real-time events | Append-only Event Log |

---

## 7. Transparent 4-Tier Memory Design

| Memory Class | Description & Examples | Storage & Expiry Rules | User Control |
| :--- | :--- | :--- | :--- |
| **Session Memory** | "Debugging Rust Sparse Merkle Tree verification" | Thread-local; compresses into rolling summary upon thread completion. | Auto-cleared |
| **User Memory** | "Prefers PowerShell, Docker, React, Tailwind, and strict Rust typing" | Persistent user preference record with source tracking and confidence score. | Edit / Delete |
| **Project Memory** | "SPV-1 AUC is $4.82B USD under ERC-3643 contract `0xUNYKORN...`" | Workspace-scoped, version-controlled fact record tied to Obsidian source. | Edit / Delete |
| **Operational Memory**| "FastAPI socket timeout on port 8790 requires process restart" | TTL-based operational metric; auto-expires after 7 days. | Purge All |

---

*Authored for Unykorn LLC by Kevan Burns, Founder, Owner & CEO.*  
*Maintained under `C:\Unykorn-Brain\00_NEURAL_KERNEL\DONK_REALTIME_ARCHITECTURE.md`.*
