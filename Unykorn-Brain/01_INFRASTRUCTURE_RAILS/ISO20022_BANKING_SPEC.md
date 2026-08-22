# ISO 20022 / Fedwire / ACH Integration Specification
**Document ID:** `SPEC-UNYKORN-BANKING-2026-V1`  
**Entity:** Unykorn LLC (Technology Rails & Software Gateway)  
**Target Counterparty:** Charter Bank & Trust / Institutional Fiduciary Custodians  

## 1. Regulatory Boundary
Unykorn LLC is purely a software and technology gateway provider. Unykorn LLC does not hold customer fiat deposits, take balance-sheet credit risk, or maintain banking custody. All escrow balances, reserve custody, and settlement finality reside exclusively with Charter Bank as the qualified depository institution of record.

## 2. Supported Formats
- Inbound Escrow Advice: `camt.054.001.08` (Real-Time Credit Notification)
- Outbound Waterfall Payouts: `pain.001.001.09` (Customer Credit Transfer Initiation)
- Daily Reconciliation: `camt.053.001.08` (Bank-to-Customer Statement)
- ACH Corporate Ingestion: NACHA CCD+ Record Type 7 (705 Addenda)
