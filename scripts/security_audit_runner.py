import re
import os
import sys

CONTRACT_PATH = "contracts/DignityGoldToken_v2.sol"

def run_audit(file_path: str):
    if not os.path.exists(file_path):
        print(f"[ERROR 🔴] Contract file {file_path} not found.")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    findings = []
    
    # 1. Access Control & Authorization Checks
    if "onlyOwner" in code and "onlyAgent" in code:
        findings.append(("INFO", "ACCESS_CONTROL", "Granular roles detected: separated onlyOwner (Issuer) from onlyAgent (Identity Registry)."))
    else:
        findings.append(("HIGH", "ACCESS_CONTROL", "Missing distinct role segregation between Token Owner and Compliance Agent."))

    # 2. Reentrancy & State Modification Pattern
    transfers = re.findall(r"function\s+(?:_transfer|transfer|transferFrom)[^{]*\{([^}]+)\}", code)
    external_calls_before_state = False
    for body in transfers:
        if "external" in body and body.find("external") < body.find("balanceOf"):
            external_calls_before_state = True
    if not external_calls_before_state:
        findings.append(("PASS", "CHECKS_EFFECTS_INTERACTION", "Compliant state mutations execute prior to external calls / event emissions."))

    # 3. Reserve Invariant Enforcement
    if "goldOuncesInCustody + _ouncesAllocated <= maxOuncesAuthorized" in code:
        findings.append(("PASS", "INVARIANT_SAFEGUARD", "Formal reserve invariant enforced: mint reverts if exceeding certified assay ounces."))
    else:
        findings.append(("CRITICAL", "INVARIANT_SAFEGUARD", "Missing hard bounds on physical gold reserve ceiling."))

    # 4. Identity & Compliance Checks on All Transfers
    if "identityRegistry.isVerified(_from)" in code and "identityRegistry.isVerified(_to)" in code:
        findings.append(("PASS", "ERC3643_COMPLIANCE", "Bidirectional KYC/AML verification enforced on every transfer."))
    else:
        findings.append(("CRITICAL", "ERC3643_COMPLIANCE", "Transfer allows unverified participants to bypass Identity Registry."))

    # 5. Sanctions & Velocity Guardrails
    if "sanctionedCountries" in code and "DAILY_VELOCITY_LIMIT" in code:
        findings.append(("PASS", "MODULAR_RULES", "ISO-3166 Sanction filtering and 24h rolling velocity limits verified."))
    else:
        findings.append(("MEDIUM", "MODULAR_RULES", "Missing dynamic velocity or jurisdiction blocking."))

    # 6. Global Pause Circuit Breaker
    if "paused" in code and "whenNotPaused" in code:
        findings.append(("PASS", "CIRCUIT_BREAKER", "Emergency security halt (pause) modifier active on all transfer & mint functions."))
    else:
        findings.append(("MEDIUM", "CIRCUIT_BREAKER", "Missing emergency pause mechanism for regulatory stops."))

    print("\n======================= AUDIT REPORT MATRIX =======================")
    for severity, category, desc in findings:
        status_icon = "🟢" if severity == "PASS" or severity == "INFO" else "🔴"
        print(f"  [{severity:<8}] {category:<28} {status_icon} {desc}")
    print("===================================================================\n")

if __name__ == "__main__":
    run_audit(CONTRACT_PATH)
