// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {MessageHashUtils} from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

contract UnykornClaimIssuer is AccessControl {
    using ECDSA for bytes32;
    using MessageHashUtils for bytes32;

    bytes32 public constant CLAIM_SIGNER_ROLE = keccak256("CLAIM_SIGNER_ROLE");

    // claimTopic => (claimSignature => isRevoked)
    mapping(uint256 => mapping(bytes => bool)) private _revokedClaims;

    event ClaimRevoked(uint256 indexed topic, bytes indexed signature);
    event ClaimUnrevoked(uint256 indexed topic, bytes indexed signature);

    error InvalidSigner();
    error ClaimAlreadyRevoked();

    constructor(address admin, address signer) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(CLAIM_SIGNER_ROLE, signer);
    }

    function isClaimRevoked(uint256 topic, bytes calldata signature) external view returns (bool) {
        return _revokedClaims[topic][signature];
    }

    function revokeClaim(uint256 topic, bytes calldata signature) external onlyRole(CLAIM_SIGNER_ROLE) {
        if (_revokedClaims[topic][signature]) revert ClaimAlreadyRevoked();
        _revokedClaims[topic][signature] = true;
        emit ClaimRevoked(topic, signature);
    }

    function isClaimValid(
        address identityAddress,
        uint256 topic,
        bytes calldata signature,
        bytes calldata data
    ) external view returns (bool) {
        if (_revokedClaims[topic][signature]) return false;

        bytes32 messageHash = keccak256(abi.encodePacked(identityAddress, topic, data));
        bytes32 ethSignedMessageHash = messageHash.toEthSignedMessageHash();
        
        address recoveredSigner = ethSignedMessageHash.recover(signature);
        return hasRole(CLAIM_SIGNER_ROLE, recoveredSigner);
    }
}
