#!/usr/bin/env python3
"""
Unykorn LLC - High-Performance Obsidian Neural Vault RAG Search Engine
Scans, indexes, and queries markdown nodes across Unykorn-Brain and Obsidian-Vault.
"""

from pathlib import Path
import os
import sys
import re

VAULT_DIR = Path(r"C:\Unykorn-Brain")

def tokenize(text):
    return re.findall(r'\w+', text.lower())

def calculate_tf_idf_query(query_text, top_k=3):
    print(f"\n[?] Querying Unykorn Neural Vault: '{query_text}'")
    
    query_tokens = tokenize(query_text)
    if not query_tokens:
        print("[!] Empty query.")
        return

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
                        "content": block.strip()
                    })
        except Exception:
            pass

    documents.sort(key=lambda x: x["score"], reverse=True)
    
    if not documents:
        print("[!] No matching nodes found in vault.")
        return

    print(f"[+] Found {len(documents)} relevant node sections across vault.")
    for idx, doc in enumerate(documents[:top_k]):
        print(f"\n--- Match {idx+1} [Source: [[{doc['source']}]]] (Relevance Score: {doc['score']}) ---")
        print(doc["content"][:600] + ("..." if len(doc["content"]) > 600 else ""))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--query":
        query_text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "What are the rules regarding custody and lending?"
        calculate_tf_idf_query(query_text)
    else:
        calculate_tf_idf_query("What is Unykorn's role in lending and custody?")
