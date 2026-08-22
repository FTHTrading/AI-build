import { useState } from "react";
import { createWalletClient, custom, parseEther } from "viem";
import { mainnet } from "viem/chains";

// --- EIP-712 DOMAIN SEPARATOR DEFINITION ---
export const UNYKORN_EIP712_DOMAIN = {
  name: "Unykorn State Engine",
  version: "1",
  chainId: 1, // Custom / Local App-Chain
  verifyingContract: "0x0000000000000000000000000000000000000000" as `0x${string}`,
} as const;

// --- TYPED DATA STRUCTURES MATCHING UNYKORN-VM ---
export const UNYKORN_EIP712_TYPES = {
  AttestRwaCollateral: [
    { name: "spvId", type: "bytes16" },
    { name: "valuationUsd", type: "uint64" },
    { name: "proofHash", type: "bytes32" },
    { name: "nonce", type: "uint64" },
  ],
  Transfer: [
    { name: "to", type: "address" },
    { name: "amount", type: "uint64" },
    { name: "nonce", type: "uint64" },
  ],
} as const;

export function useUnykornSigner() {
  const [account, setAccount] = useState<`0x${string}` | null>(null);
  const [isSigning, setIsSigning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Connect Web3 Wallet
  const connectWallet = async () => {
    if (typeof window === "undefined" || !(window as any).ethereum) {
      setError("No Web3 wallet extension found. Install MetaMask or Rabby.");
      return null;
    }

    try {
      const client = createWalletClient({
        chain: mainnet,
        transport: custom((window as any).ethereum),
      });

      const [address] = await client.requestAddresses();
      setAccount(address);
      setError(null);
      return address;
    } catch (err: any) {
      setError(err.message || "Wallet connection rejected.");
      return null;
    }
  };

  // Sign and submit RWA Collateral Attestation
  const signAndSubmitAttestation = async (
    spvId: `0x${string}`, // 16-byte hex
    valuationUsd: bigint,
    proofHash: `0x${string}`, // 32-byte hex
    nonce: bigint
  ) => {
    let currentAccount = account;
    if (!currentAccount) {
      const connected = await connectWallet();
      if (!connected) return;
      currentAccount = connected;
    }

    setIsSigning(true);
    setError(null);

    try {
      const client = createWalletClient({
        chain: mainnet,
        transport: custom((window as any).ethereum),
      });

      // 1. Request EIP-712 Signature
      const signature = await client.signTypedData({
        account: currentAccount!,
        domain: UNYKORN_EIP712_DOMAIN,
        types: UNYKORN_EIP712_TYPES,
        primaryType: "AttestRwaCollateral",
        message: {
          spvId,
          valuationUsd,
          proofHash,
          nonce,
        },
      });

      // 2. Dispatch to Unykorn Gateway on Port 8790
      const res = await fetch("http://127.0.0.1:8790/v1/chain/submit-tx", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender: currentAccount,
          receiver: "0xUNYKORN_TREASURY_GATEWAY",
          payload: `ATTEST_SPV=${spvId}; VALUE=$${valuationUsd}`,
          truth_proof: {
            category: "RwaAssetAttestation",
            claim_hash: proofHash,
            confidence_score: 99,
            evidence_uri: "eip712://wallet/signature",
            signature,
          },
          nonce: Number(nonce),
          signature,
        }),
      });

      const data = await res.json();
      setIsSigning(false);
      return { signature, txResponse: data };
    } catch (err: any) {
      setIsSigning(false);
      setError(err.message || "Failed to sign or submit transaction.");
      throw err;
    }
  };

  return {
    account,
    isSigning,
    error,
    connectWallet,
    signAndSubmitAttestation,
  };
}
