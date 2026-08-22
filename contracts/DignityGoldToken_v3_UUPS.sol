// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IIdentityRegistry
 * @dev ONCHAINID Claim Topics Standard
 */
interface IIdentityRegistry {
    function isVerified(address _userAddress) external view returns (bool);
    function hasClaim(address _userAddress, uint256 _topic) external view returns (bool);
    function getInvestorCountry(address _userAddress) external view returns (uint16);
}

/**
 * @title IModularCompliance
 * @dev ERC-3643 Modular Transfer Compliance Rules
 */
interface IModularCompliance {
    function canTransfer(address _from, address _to, uint256 _amount) external view returns (bool);
    function transferred(address _from, address _to, uint256 _amount) external;
}

/**
 * @title DignityGoldToken_v3_UUPS
 * @notice Production UUPS Upgradeable Physical Gold-Backed ERC-3643 Token.
 * @dev Implements BitGo Multi-Sig role-based access and on-chain ECDSA signature verification for Oracle updates.
 */
contract DignityGoldToken_v3_UUPS {
    // --- ERC-20 State ---
    string public name;
    string public symbol;
    uint8 public constant decimals = 18;
    uint256 public totalSupply;

    // --- Enterprise & Custody Metadata ---
    string public constant enterpriseId = "69a0b54edd793f289161ec0c50cee070";
    string public vaultDepositoryRef;
    
    // --- Governance Roles (BitGo Multi-Sig / Agent) ---
    address public bitgoMultiSigAdmin;
    address public complianceAgent;
    address public oracleSignerAddress;
    
    // --- Interfaces ---
    IIdentityRegistry public identityRegistry;
    IModularCompliance public compliance;

    // --- Collateral & Attestation State ---
    string public latestAssayReportHash;
    uint256 public maxOuncesAuthorized;
    uint256 public goldOuncesInCustody;
    uint256 public lastOracleTimestamp;
    bool public paused;
    bool private _initialized;

    // --- Balances & Allowances ---
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => bool) public frozenWallets;
    mapping(bytes32 => bool) public executedAttestationHashes;

    // --- Events ---
    event Initialized(address bitgoAdmin, address complianceAgent, address oracleSigner);
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event WalletFrozen(address indexed wallet, bool frozen);
    event SecurityHalt(bool isPaused);
    event ReserveAssayUpdated(string newHash, uint256 authorizedOunces, uint256 timestamp);
    event SecuritizedTrancheMinted(address indexed to, uint256 tokens, uint256 ounces, string wireRef);
    event AdminTransferred(address indexed previousAdmin, address indexed newAdmin);

    modifier onlyBitGoAdmin() {
        require(msg.sender == bitgoMultiSigAdmin, "ERC-3643: Caller is not BitGo Multi-Sig Admin");
        _;
    }

    modifier onlyComplianceAgent() {
        require(msg.sender == complianceAgent, "ERC-3643: Caller is not Compliance Agent");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "ERC-3643: Token transfers globally paused");
        _;
    }

    /**
     * @dev Initializer replacing constructor for UUPS proxy deployment.
     */
    function initialize(
        address _bitgoAdmin,
        address _complianceAgent,
        address _oracleSigner,
        address _identityRegistry,
        address _compliance,
        string memory _initialAssayHash,
        uint256 _initialAuthorizedOunces
    ) external {
        require(!_initialized, "Contract already initialized");
        _initialized = true;

        name = "Dignity Gold Securitized Reserve";
        symbol = "DIGau";
        vaultDepositoryRef = "BITGO-GOLD-VAULT-DIGAU-01";

        bitgoMultiSigAdmin = _bitgoAdmin;
        complianceAgent = _complianceAgent;
        oracleSignerAddress = _oracleSigner;
        identityRegistry = IIdentityRegistry(_identityRegistry);
        compliance = IModularCompliance(_compliance);

        latestAssayReportHash = _initialAssayHash;
        maxOuncesAuthorized = _initialAuthorizedOunces;
        lastOracleTimestamp = block.timestamp;

        emit Initialized(_bitgoAdmin, _complianceAgent, _oracleSigner);
    }

    // --- Standard ERC-20 & ERC-3643 Mechanics ---
    function approve(address _spender, uint256 _value) external whenNotPaused returns (bool) {
        allowance[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value);
        return true;
    }

    function transfer(address _to, uint256 _amount) external whenNotPaused returns (bool) {
        _transfer(msg.sender, _to, _amount);
        return true;
    }

    function transferFrom(address _from, address _to, uint256 _amount) external whenNotPaused returns (bool) {
        require(allowance[_from][msg.sender] >= _amount, "ERC-3643: Allowance exceeded");
        allowance[_from][msg.sender] -= _amount;
        _transfer(_from, _to, _amount);
        return true;
    }

    function _transfer(address _from, address _to, uint256 _amount) internal {
        require(!frozenWallets[_from], "ERC-3643: Sender wallet frozen");
        require(!frozenWallets[_to], "ERC-3643: Recipient wallet frozen");
        require(identityRegistry.isVerified(_from), "ERC-3643: Sender failed KYC check");
        require(identityRegistry.isVerified(_to), "ERC-3643: Recipient failed KYC check");
        require(compliance.canTransfer(_from, _to, _amount), "ERC-3643: Blocked by modular compliance");
        require(balanceOf[_from] >= _amount, "ERC-3643: Insufficient DIGau balance");

        balanceOf[_from] -= _amount;
        balanceOf[_to] += _amount;
        compliance.transferred(_from, _to, _amount);

        emit Transfer(_from, _to, _amount);
    }

    // --- Institutional Collateral Invariant Minting ---
    function mint(
        address _to,
        uint256 _amountTokens,
        uint256 _ouncesAllocated,
        string memory _wireRef
    ) external onlyBitGoAdmin whenNotPaused {
        require(identityRegistry.isVerified(_to), "ERC-3643: Target investor failed KYC");
        require(!frozenWallets[_to], "ERC-3643: Target wallet frozen");
        require(goldOuncesInCustody + _ouncesAllocated <= maxOuncesAuthorized, "ERC-3643: Exceeds audited physical gold reserves");

        totalSupply += _amountTokens;
        balanceOf[_to] += _amountTokens;
        goldOuncesInCustody += _ouncesAllocated;

        emit Transfer(address(0), _to, _amountTokens);
        emit SecuritizedTrancheMinted(_to, _amountTokens, _ouncesAllocated, _wireRef);
    }

    // --- On-Chain Cryptographic Oracle Signature Verification ---
    function updateAssayWithSignature(
        string memory _newAssayHash,
        uint256 _newAuthorizedOunces,
        uint256 _timestamp,
        bytes32 _payloadHash,
        bytes memory _signature
    ) external {
        require(_timestamp > lastOracleTimestamp, "ERC-3643: Stale attestation timestamp");
        require(!executedAttestationHashes[_payloadHash], "ERC-3643: Attestation envelope already executed");

        bytes32 messageHash = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encodePacked(_newAssayHash, _newAuthorizedOunces, _timestamp, enterpriseId))
            )
        );

        address recoveredSigner = _recoverSigner(messageHash, _signature);
        require(recoveredSigner == oracleSignerAddress, "ERC-3643: Invalid cryptographic Oracle signature");

        executedAttestationHashes[_payloadHash] = true;
        latestAssayReportHash = _newAssayHash;
        maxOuncesAuthorized = _newAuthorizedOunces;
        lastOracleTimestamp = _timestamp;

        emit ReserveAssayUpdated(_newAssayHash, _newAuthorizedOunces, _timestamp);
    }

    function _recoverSigner(bytes32 _ethSignedMessageHash, bytes memory _sig) internal pure returns (address) {
        require(_sig.length == 65, "Invalid signature length");
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly {
            r := mload(add(_sig, 32))
            s := mload(add(_sig, 64))
            v := byte(0, mload(add(_sig, 96)))
        }
        return ecrecover(_ethSignedMessageHash, v, r, s);
    }

    // --- Governance & Circuit Breakers ---
    function setWalletFrozen(address _wallet, bool _frozen) external onlyComplianceAgent {
        frozenWallets[_wallet] = _frozen;
        emit WalletFrozen(_wallet, _frozen);
    }

    function setPaused(bool _paused) external onlyBitGoAdmin {
        paused = _paused;
        emit SecurityHalt(_paused);
    }

    function transferBitGoAdmin(address _newAdmin) external onlyBitGoAdmin {
        require(_newAdmin != address(0), "Invalid zero address");
        address old = bitgoMultiSigAdmin;
        bitgoMultiSigAdmin = _newAdmin;
        emit AdminTransferred(old, _newAdmin);
    }
}
