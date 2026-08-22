// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {IIdentityRegistry} from "./IIdentityRegistry.sol";
import {UnykornClaimIssuer} from "./UnykornClaimIssuer.sol";

contract UnykornIdentityRegistry is IIdentityRegistry, AccessControl {
    bytes32 public constant REGISTRY_AGENT_ROLE = keccak256("REGISTRY_AGENT_ROLE");

    struct InvestorIdentity {
        address identityAddress;
        uint16 countryCode;
        bool isWhitelisted;
    }

    // investorWallet => InvestorIdentity
    mapping(address => InvestorIdentity) private _identities;
    
    // Trusted Claim Issuers for specific claim topics
    // topic => claimIssuerAddress
    mapping(uint256 => address) public trustedClaimIssuers;

    // Events
    event IdentityRegistered(address indexed investorAddress, address indexed identityAddress, uint16 countryCode);
    event IdentityRemoved(address indexed investorAddress);
    event CountryUpdated(address indexed investorAddress, uint16 newCountryCode);
    event TrustedIssuerSet(uint256 indexed topic, address indexed issuer);

    // Custom Errors
    error InvestorNotRegistered(address investor);
    error ZeroAddressDetected();

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(REGISTRY_AGENT_ROLE, admin);
    }

    function setTrustedClaimIssuer(uint256 topic, address issuer) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (issuer == address(0)) revert ZeroAddressDetected();
        trustedClaimIssuers[topic] = issuer;
        emit TrustedIssuerSet(topic, issuer);
    }

    function registerIdentity(
        address investorAddress,
        address identityAddress,
        uint16 countryCode
    ) external onlyRole(REGISTRY_AGENT_ROLE) {
        if (investorAddress == address(0) || identityAddress == address(0)) revert ZeroAddressDetected();

        _identities[investorAddress] = InvestorIdentity({
            identityAddress: identityAddress,
            countryCode: countryCode,
            isWhitelisted: true
        });

        emit IdentityRegistered(investorAddress, identityAddress, countryCode);
    }

    function removeIdentity(address investorAddress) external onlyRole(REGISTRY_AGENT_ROLE) {
        if (_identities[investorAddress].identityAddress == address(0)) revert InvestorNotRegistered(investorAddress);
        
        delete _identities[investorAddress];
        emit IdentityRemoved(investorAddress);
    }

    function updateCountry(address investorAddress, uint16 newCountryCode) external onlyRole(REGISTRY_AGENT_ROLE) {
        if (_identities[investorAddress].identityAddress == address(0)) revert InvestorNotRegistered(investorAddress);
        
        _identities[investorAddress].countryCode = newCountryCode;
        emit CountryUpdated(investorAddress, newCountryCode);
    }

    // --- IIdentityRegistry Interface Implementations ---

    function isVerified(address investorAddress) external view override returns (bool) {
        return _identities[investorAddress].isWhitelisted;
    }

    function identity(address investorAddress) external view override returns (address) {
        return _identities[investorAddress].identityAddress;
    }

    function investorCountry(address investorAddress) external view override returns (uint16) {
        return _identities[investorAddress].countryCode;
    }
}
