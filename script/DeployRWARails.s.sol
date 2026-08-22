// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {UnykornPermissionedToken} from "../contracts/UnykornPermissionedToken.sol";

contract DeployRWARails is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address adminAddress = vm.envAddress("ADMIN_ADDRESS");
        address mockIdentityRegistry = vm.envAddress("IDENTITY_REGISTRY");
        address mockCompliance = vm.envAddress("COMPLIANCE_ENGINE");

        vm.startBroadcast(deployerPrivateKey);

        UnykornPermissionedToken token = new UnykornPermissionedToken(
            "Unykorn Institutional Senior Debt SPV-1",
            "U-SND1",
            18,
            adminAddress,
            mockIdentityRegistry,
            mockCompliance
        );

        console2.log("Unykorn RWA Token Deployed at:", address(token));
        console2.log("Admin Assigned:", adminAddress);

        vm.stopBroadcast();
    }
}
