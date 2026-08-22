// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IIdentityRegistry {
    function isVerified(address _userAddress) external view returns (bool);
    function registerIdentity(address _userAddress, address _identityContract, uint16 _country) external;
}

interface IModularCompliance {
    function canTransfer(address _from, address _to, uint256 _amount) external view returns (bool);
}

/**
 * @title DignityGoldSecuritizedToken
 * @notice ERC-3643 Physical Gold-Backed Security Token (DIGau)
 * @dev Anchored to BitGo Qualified Custody Vault reserves and audited assay certificates.
 */
contract DignityGoldSecuritizedToken {
    string public name = "Dignity Gold Securitized Reserve";
    string public symbol = "DIGau";
    uint8 public constant decimals = 18;
    uint256 public totalSupply;

    address public owner;
    IIdentityRegistry public identityRegistry;
    IModularCompliance public compliance;

    string public custodyEnclaveId = "69a0b54edd793f289161ec0c50cee070";
    string public vaultDepositoryRef = "BITGO-GOLD-VAULT-DIGAU-01";
    string public latestAssayReportHash;
    uint256 public goldOuncesInCustody;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => bool) public frozenWallets;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event GoldReserveMinted(address indexed investor, uint256 amountTokens, string bitgoSettlementRef, uint256 goldOuncesAllocated);
    event AssayReportUpdated(string oldHash, string newHash, uint256 totalOunces);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only Issuer Authority");
        _;
    }

    constructor(
        address _identityRegistry,
        address _compliance,
        string memory _assayReportHash,
        uint256 _initialGoldOunces
    ) {
        owner = msg.sender;
        identityRegistry = IIdentityRegistry(_identityRegistry);
        compliance = IModularCompliance(_compliance);
        latestAssayReportHash = _assayReportHash;
        goldOuncesInCustody = _initialGoldOunces;
    }

    function mint(
        address _to,
        uint256 _amountTokens,
        string memory _bitgoSettlementRef,
        uint256 _goldOuncesAllocated
    ) external onlyOwner {
        require(identityRegistry.isVerified(_to), "ERC-3643: Target investor failed KYC/AML claims");
        require(!frozenWallets[_to], "ERC-3643: Target wallet frozen");

        totalSupply += _amountTokens;
        balanceOf[_to] += _amountTokens;
        goldOuncesInCustody += _goldOuncesAllocated;

        emit Transfer(address(0), _to, _amountTokens);
        emit GoldReserveMinted(_to, _amountTokens, _bitgoSettlementRef, _goldOuncesAllocated);
    }

    function transfer(address _to, uint256 _amount) external returns (bool) {
        require(identityRegistry.isVerified(msg.sender), "ERC-3643: Sender failed KYC check");
        require(identityRegistry.isVerified(_to), "ERC-3643: Recipient failed KYC check");
        require(compliance.canTransfer(msg.sender, _to, _amount), "ERC-3643: Transfer blocked by compliance rules");
        require(balanceOf[msg.sender] >= _amount, "ERC-3643: Insufficient DIGau balance");

        balanceOf[msg.sender] -= _amount;
        balanceOf[_to] += _amount;

        emit Transfer(msg.sender, _to, _amount);
        return true;
    }

    function updateAssayAudit(string memory _newAssayHash, uint256 _auditedTotalOunces) external onlyOwner {
        string memory old = latestAssayReportHash;
        latestAssayReportHash = _newAssayHash;
        goldOuncesInCustody = _auditedTotalOunces;
        emit AssayReportUpdated(old, _newAssayHash, _auditedTotalOunces);
    }
}
