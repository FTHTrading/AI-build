// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {UnykornPermissionedToken} from "../contracts/UnykornPermissionedToken.sol";
import {UnykornIdentityRegistry} from "../contracts/UnykornIdentityRegistry.sol";
import {UnykornClaimIssuer} from "../contracts/UnykornClaimIssuer.sol";

contract DeployFullTokenizationSuite is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address adminAddress = vm.envAddress("ADMIN_ADDRESS");
        address signerAddress = vm.envAddress("CLAIM_SIGNER_ADDRESS");
        address complianceEngine = vm.envAddress("COMPLIANCE_ENGINE");

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy Claim Issuer (Signer)
        UnykornClaimIssuer claimIssuer = new UnykornClaimIssuer(adminAddress, signerAddress);
        console2.log("UnykornClaimIssuer Deployed at:", address(claimIssuer));

        // 2. Deploy Identity Registry
        UnykornIdentityRegistry identityRegistry = new UnykornIdentityRegistry(adminAddress);
        console2.log("UnykornIdentityRegistry Deployed at:", address(identityRegistry));

        // 3. Deploy Permissioned RWA Token
        UnykornPermissionedToken token = new UnykornPermissionedToken(
            "Unykorn Institutional Senior Debt SPV-1",
            "U-SND1",
            18,
            adminAddress,
            address(identityRegistry),
            complianceEngine
        );
        console2.log("UnykornPermissionedToken Deployed at:", address(token));

        vm.stopBroadcast();
    }
}
