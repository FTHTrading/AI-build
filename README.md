# 🦄 UNYKORN LLC — AI-BUILD: ENTERPRISE AI ENGINE & NEURAL RAG GATEWAY

[![Unykorn Status](https://img.shields.io/badge/System-ACTIVE-4ade80?style=for-the-badge&logo=solidity)](https://unykorn.com)
[![Hardware GPU](https://img.shields.io/badge/Hardware-NVIDIA_RTX_5090_24GB-76b900?style=for-the-badge&logo=nvidia)](https://nvidia.com)
[![Vault Notes](https://img.shields.io/badge/Neural_Vault-2%2C461_Notes-8a2be2?style=for-the-badge&logo=obsidian)](file:///C:/Unykorn-Brain)
[![Security Level](https://img.shields.io/badge/Security-INSTITUTIONAL_GRADE-dc2626?style=for-the-badge&logo=gitbook)](https://github.com/FTHTrading/AI-build)

---

## 📌 Executive Summary & Governance

**Entity**: Unykorn LLC (Wyoming LLC, filed July 1, 2026 | EIN 42-3536633 | ISO MIC UBEC)  
**Leadership**: Kevan Burns (Founder, Owner & CEO)  
**Core Purpose**: Enterprise-grade infrastructure gateway, protocol rails, compliance smart contract suites, and autonomous neural execution brain for Real-World Asset (RWA) tokenization, alternative credit facilities, and multi-rail settlements.

> [!IMPORTANT]
> **Entity Boundary Constraint**: Unykorn LLC is an **infrastructure, software, and technology gateway provider**. Unykorn LLC is **NOT** a direct lender, broker-dealer, or qualified custodian. All custody, escrow, and settlement operations integrate with qualified institutional third-party custodians (e.g. BitGo, XRPL Escrows, Stellar Trustlines).

---

## 🗺️ Master Table of Contents

- [📌 Executive Summary & Governance](#-executive-summary--governance)
- [🎨 Color-Coded Module System Architecture](#-color-coded-module-system-architecture)
  - [🔵 Module 01: Gateway Rails & System Kernel](#-module-01-gateway-rails--system-kernel)
  - [🟢 Module 02: RWA Tokenization & Compliance Contracts](#-module-02-rwa-tokenization--compliance-contracts)
  - [🟣 Module 03: Local AI Engine & RTX 5090 Acceleration](#-module-03-local-ai-engine--rtx-5090-acceleration)
  - [🟡 Module 04: Episodic Memory & Neural Vault RAG](#-module-04-episodic-memory--neural-vault-rag)
  - [🔴 Module 05: Multi-Rail Security & Operational Guardrails](#-module-05-multi-rail-security--operational-guardrails)
- [⚙️ Microservices & Network Port Matrix](#️-microservices--network-port-matrix)
- [🧠 Neural Vault Folder Hierarchy (`/Unykorn-Brain/`)](#-neural-vault-folder-hierarchy-unykorn-brain)
- [🚀 Local Setup & Git Quickstart](#-local-setup--git-quickstart)
- [📄 License & Institutional Legal Notice](#-license--institutional-legal-notice)

---

## 🎨 Color-Coded Module System Architecture

```
+-----------------------------------------------------------------------------------+
|                            UNYKORN ENTERPRISE ECOSYSTEM                           |
+-------------------+-------------------+-------------------+-----------------------+
| 🔵 GATEWAY RAILS  | 🟢 RWA COMPLIANCE | 🟣 AI ACCELERATOR | 🟡 NEURAL VAULT RAG   |
|   (Port 8790)     | (ERC-3643 / SPV)  |  (RTX 5090 GPU)   |  (2,461 Vault Nodes)  |
+-------------------+-------------------+-------------------+-----------------------+
| 🔴 MULTI-RAIL SECURITY & INSTITUTIONAL CUSTODY (BitGo / XRPL / Stellar / EVM)     |
+-----------------------------------------------------------------------------------+
```

---

### 🔵 Module 01: Gateway Rails & System Kernel
* **Core Responsibility**: Rest API Gateways, Command Server Bridges, and client-server orchestration.
* **Primary Tech Stack**: TypeScript, Node.js (CommonJS), Express / Custom HTTP daemons, WebSockets.
* **Key Components**:
  * `clawd-command-server.js` — Core HTTP Command Gateway listening on port `8790`.
  * `clawd-command-bridge.js` — Microservice process watcher and daemon health manager.
  * `web-dashboard.html` — Executive Superpowers Launchpad & Telemetry Console.

---

### 🟢 Module 02: RWA Tokenization & Compliance Contracts
* **Core Responsibility**: Permissioned smart contract suites, Special Purpose Vehicle (SPV) structures, and dividend distribution logic.
* **Primary Tech Stack**: Solidity (v0.8.20+), Foundry, Hardhat, OpenZeppelin Permissioned Contracts.
* **Key Standards**:
  * **ERC-3643 (T-REX)** & **ERC-1400**: On-chain identity verification (`isVerified`) and transfer permission hooks (`canTransfer`).
  * **Multi-Tranche Waterfall Contracts**: Senior Secured, Mezzanine, and Equity debt distribution engines.
  * **AUC Assets**: $4,820,000,000 registered across 155 verified on-chain assets.

---

### 🟣 Module 03: Local AI Engine & RTX 5090 Acceleration
* **Core Responsibility**: On-premise private AI execution, LLM inferencing, and video generation.
* **Primary Hardware**: **NVIDIA GeForce RTX 5090 (24 GB VRAM)** | 64 GB System RAM.
* **Key Microservices**:
  * **Ollama LLM Engine** (`http://127.0.0.1:11434`) — Powering `unykorn-clawd:14b` & `nomic-embed-text`.
  * **Open WebUI Portal** (`http://127.0.0.1:3000`) — Enterprise Chat Interface & Custom Tool execution.
  * **ComfyUI Server** (`http://127.0.0.1:8188`) — Wan 2.2 Text-to-Video & Image-to-Video generation pipeline.

---

### 🟡 Module 04: Episodic Memory & Neural Vault RAG
* **Core Responsibility**: Continuous background learning, vault sanitization, vector search indexing, and execution logging.
* **Primary Engine**: `unykorn_mcp_agentic_rag.py` & `sync_unykorn_brain.ps1`.
* **Key Components**:
  * `C:\Unykorn-Brain` — Primary 2,461-node markdown knowledge graph.
  * `04_EPISODIC_MEMORY/DAILY_TRANSACTIONS/` — Immutable date-stamped action logs (`YYYY-MM-DD.md`).
  * `04_EPISODIC_MEMORY/DECISION_REGISTRY.md` — DataviewJS executive decision dashboard.

---

### 🔴 Module 05: Multi-Rail Security & Operational Guardrails
* **Core Responsibility**: Multi-chain wallet routing, institutional qualified custody hooks, and deterministic safety checks.
* **Key Integrations**:
  * **BitGo Enterprise Custody**: Segregated accounts & Escrow capital formation.
  * **Multi-Chain Wallet Matrix**: Solana, EVM (Ethereum, Base, Polygon), XRPL, Stellar, Apostle Chain (ATP 7332).
  * **Deterministic Code Rules**: Zero placeholders (`// TODO`), explicit Role-Based Access Control (`Ownable2Step`), and reentrancy protection.

---

## ⚙️ Microservices & Network Port Matrix

| Service | Port | Description | Hardware Anchor | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Clawd Control Center** | `8790` | System Command Gateway & RAG API | Host / Local Node | **ONLINE** 🟢 |
| **Open WebUI Portal** | `3000` | Enterprise Chat & Custom Tool Interface | Docker / Host | **ONLINE** 🟢 |
| **Ollama LLM Engine** | `11434` | Private LLM & Vector Embedding API | RTX 5090 (24GB VRAM) | **ONLINE** 🟢 |
| **ComfyUI AI Video** | `8188` | Wan 2.2 Photorealistic Video Pipeline | RTX 5090 (24GB VRAM) | **ONLINE** 🟢 |
| **Legacy Clawdbot Bridge**| `8089` | Backward-compatibility API bridge | Local Node | **ONLINE** 🟢 |
| **NeMo-Claw Daemon** | `8300` | Security & Guardrail Telemetry | Local Node | **ONLINE** 🟢 |

---

## 🧠 Neural Vault Folder Hierarchy (`/Unykorn-Brain/`)

```text
C:\Unykorn-Brain\
├── 00_NEURAL_KERNEL/
│   ├── CORE_IDENTITY.md              <-- Governance, CEO, persona, voice
│   ├── SYSTEM_CONSTRAINTS.md         <-- Entity boundaries, no direct custody/lending
│   └── ONTOLOGY_INDEX.md             <-- Master link graph of all nodes
├── 01_INFRASTRUCTURE_RAILS/
│   ├── ERC3643_COMPLIANCE.md         <-- Permissioned contracts, DIDs, KYC registries
│   ├── MULTI_TRANCHE_WATERFALLS.md   <-- Senior/Mezz/Equity debt distribution logic
│   └── CUSTODY_GATEWAYS.md           <-- Institutional qualified custody integrations
├── 02_DEVOPS_AUTOMATION/
│   ├── DOCKER_COMPOSE_SPEC.md        <-- Microservices, node sync configs
│   ├── POWERSHELL_WSL_DAEMONS.md     <-- Automation loops, background workers
│   └── AGENTIC_ROUTING.md            <-- Context injection rules & memory tiers
├── 03_ASSET_REGISTRIES/
│   ├── SPV_STRUCTURES.md             <-- Special Purpose Vehicle models ($4.82B AUC)
│   ├── RWA_PIPELINES.md              <-- Private credit, clean energy, mining pipelines
│   └── PARTNERS_DEALFLOW.md          <-- Institutional dealflow & strategic accounts
└── 04_EPISODIC_MEMORY/
    ├── DAILY_TRANSACTIONS/           <-- Immutable daily action logs (YYYY-MM-DD.md)
    └── DECISION_REGISTRY.md          <-- DataviewJS executive decision dashboard
```

---

## 🚀 Local Setup & Git Quickstart

### 1. Initialize Local Repository & Connect Remote

```bash
# Navigate to project directory
cd C:\Users\Kevan\AI-build

# Initialize git repository
git init
git add README.md
git commit -m "feat: initialize Unykorn AI Engine core architecture & README"

# Set main branch and remote origin
git branch -M main
git remote add origin https://github.com/FTHTrading/AI-build.git

# Push to GitHub
git push -u origin main
```

---

## 📄 License & Institutional Legal Notice

**Copyright © 2026 Unykorn LLC. All Rights Reserved.**  
All software, smart contracts, specifications, and neural vault documentation are proprietary assets of Unykorn LLC. Unykorn LLC provides software technology and infrastructure rails exclusively.
