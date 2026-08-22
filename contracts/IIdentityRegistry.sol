// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IIdentityRegistry {
    function isVerified(address investorAddress) external view returns (bool);
    function identity(address investorAddress) external view returns (address);
    function investorCountry(address investorAddress) external view returns (uint16);
}
