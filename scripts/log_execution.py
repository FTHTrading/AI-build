#!/usr/bin/env python3
"""
Unykorn LLC - Episodic Vault Logger
Automates logging of AI execution runs into the Obsidian Neural Vault.
"""

from datetime import datetime
from pathlib import Path
import os
import sys

# Configuration: Update with your local Obsidian vault root
VAULT_ROOT = Path(os.getenv("UNYKORN_VAULT_PATH", "C:/Unykorn-Brain"))
DAILY_LOG_DIR = VAULT_ROOT / "04_EPISODIC_MEMORY" / "DAILY_TRANSACTIONS"


def get_daily_template(date_str: str) -> str:
    return f"""---
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


def append_run_log(
    run_title: str,
    module_node: str,
    command: str,
    summary: str,
    artifact_name: str = "N/A",
    status: str = "COMPLETED",
    session_id: str = "SESSION-AUTO",
) -> Path:
    """Appends an execution run into today's Markdown transaction log."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%H:%M:%S")

    DAILY_LOG_DIR.mkdir(parents=True, exist_ok=True)
    daily_file = DAILY_LOG_DIR / f"{date_str}.md"

    # Initialize file if it doesn't exist today
    if not daily_file.exists():
        with open(daily_file, "w", encoding="utf-8") as f:
            f.write(get_daily_template(date_str))

    entry_block = f"""
### [{timestamp_str}] - {run_title}
- **Session ID**: `{session_id}`
- **Module Context**: [[{module_node}]]
- **Trigger / Command**: `{command}`
- **Executive Directives Applied**:
  - Validated under [[CORE_IDENTITY]] (Kevan Burns, Founder/Owner/CEO).
  - Enforced [[SYSTEM_CONSTRAINTS]] (Infrastructure & Tech Rails only).
- **Execution Payload & Artifacts**:
  - **Artifact Generated**: `{artifact_name}`
  - **Status**: `{status}`
- **Architectural Notes**:
  > {summary}

---
"""

    with open(daily_file, "a", encoding="utf-8") as f:
        f.write(entry_block)

    # Mirror log entry to Obsidian Vault mirror if present
    try:
        obsidian_mirror = Path("C:/Users/Kevan/Obsidian-Vault/Unykorn-Brain/04_EPISODIC_MEMORY/DAILY_TRANSACTIONS") / f"{date_str}.md"
        obsidian_mirror.parent.mkdir(parents=True, exist_ok=True)
        with open(obsidian_mirror, "a", encoding="utf-8") as f:
            f.write(entry_block)
    except Exception:
        pass

    return daily_file


if __name__ == "__main__":
    # Test execution run
    log_path = append_run_log(
        run_title="Smart Contract Deployment - ERC3643 Gateway",
        module_node="ERC3643_COMPLIANCE",
        command="forge script script/DeployRWARails.s.sol --broadcast",
        summary="Deployed permissioned compliance registry hook for SPV asset-backed debt tranches.",
        artifact_name="UnykornIdentityRegistry.sol",
        status="SUCCESS",
        session_id="RUN-2026-0822-01",
    )
    print(f"[+] Execution log successfully appended to: {log_path}")
