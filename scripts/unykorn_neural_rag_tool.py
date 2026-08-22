"""
title: Unykorn Neural Vault Engine
author: Unykorn LLC
author_url: https://unykorn.com
description: Queries the local Obsidian Neural Vault (Port 8790) and logs execution conclusions directly into DAILY_TRANSACTIONS.
required_open_webui_version: 0.4.0
version: 2.0.0
license: Proprietary
"""

from typing import Any, Callable, Dict, Optional
from pydantic import BaseModel, Field
import requests


class Tools:

    class Valves(BaseModel):
        QUERY_ENDPOINT: str = Field(
            default="http://host.docker.internal:8790/v1/vault/query",
            description="Clawd Command Server RAG query URL.",
        )
        LOG_ENDPOINT: str = Field(
            default="http://host.docker.internal:8790/v1/vault/log",
            description="Clawd Command Server Transaction Log URL.",
        )
        DEFAULT_TOP_K: int = Field(
            default=3,
            description="Default number of architectural nodes to retrieve.",
        )
        REQUEST_TIMEOUT: int = Field(
            default=15,
            description="HTTP timeout in seconds for API calls.",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def query_unykorn_brain(
        self,
        query: str,
        top_k: Optional[int] = None,
        __event_emitter__: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> str:
        """Query the Unykorn Neural Vault for institutional context, smart contract specs (ERC-3643), SPV parameters, and system guidelines.

        :param query: The search query or concept to look up in the Obsidian
          vault.
        :param top_k: Number of relevant knowledge chunks to retrieve.
        :return: Formatted markdown string containing retrieved neural nodes.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Querying Neural Vault for: '{query}'...",
                        "done": False,
                    },
                }
            )

        limit = top_k if top_k is not None else self.valves.DEFAULT_TOP_K
        payload = {"query": query, "top_k": limit}

        try:
            res = requests.post(
                self.valves.QUERY_ENDPOINT,
                json=payload,
                timeout=self.valves.REQUEST_TIMEOUT,
            )
            res.raise_for_status()
            data = res.json()
            results = data.get("results", [])

            if not results:
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "Vault search completed (No matches).",
                                "done": True,
                            },
                        }
                    )
                return f"No relevant nodes found in Neural Vault for: '{query}'."

            output = [
                f"### Unykorn Neural Brain Retrieval (Query: '{query}')\n"
            ]
            for idx, item in enumerate(results, 1):
                output.append(
                    f"#### [{idx}] Node: `[[{item.get('source_node')}]]` (Dist: {item.get('distance', 0.0):.4f})\n{item.get('content', '').strip()}\n"
                )

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Retrieved {len(results)} nodes.",
                            "done": True,
                        },
                    }
                )

            return "\n---\n".join(output)

        except Exception as e:
            return f"Error querying Neural Vault: {str(e)}"

    async def log_transaction_to_vault(
        self,
        title: str,
        module_node: str,
        command_or_prompt: str,
        summary: str,
        artifact_name: str = "N/A",
        status: str = "COMPLETED",
        session_id: str = "OPENWEBUI-CHAT",
        __event_emitter__: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> str:
        """Write an architectural decision, code artifact, or task conclusion directly into the daily episodic transaction ledger in Obsidian.

        :param title: Short title of the execution run or decision (e.g. 'Deploy Tranche Contract').
        :param module_node: Target module wikilink name (e.g. 'ERC3643_COMPLIANCE', 'SPV_STRUCTURES', 'DEVOPS_AUTOMATION').
        :param command_or_prompt: The user query, directive, or script executed.
        :param summary: Detailed architectural notes and results of the session.
        :param artifact_name: Name of any file/contract produced (or 'N/A').
        :param status: 'COMPLETED', 'SUCCESS', 'FAILED', or 'PENDING'.
        :param session_id: Optional tracking identifier.
        :return: Confirmation message with recorded timestamp and log file path.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Recording transaction to daily ledger: '{title}'...",
                        "done": False,
                    },
                }
            )

        payload = {
            "title": title,
            "module_node": module_node,
            "command_or_prompt": command_or_prompt,
            "summary": summary,
            "artifact_name": artifact_name,
            "status": status,
            "session_id": session_id,
        }

        try:
            res = requests.post(
                self.valves.LOG_ENDPOINT,
                json=payload,
                timeout=self.valves.REQUEST_TIMEOUT,
            )
            res.raise_for_status()
            data = res.json()

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Transaction recorded at {data.get('timestamp')}.",
                            "done": True,
                        },
                    }
                )

            return f"**Log Appended**: Registered `{title}` in `[[{module_node}]]` at `{data.get('timestamp')}`. Log File: `{data.get('log_file')}`"

        except Exception as e:
            return f"Failed to record transaction log: {str(e)}"
