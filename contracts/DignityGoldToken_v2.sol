// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @dev ONCHAINID Claim Topics Standard
 * 10101 = KYC Identity Verified
 * 10102 = AML / Sanctions Screened
 * 10103 = Qualified Institutional / Accredited Investor
 */
interface IIdentityRegistry {
    function isVerified(address _userAddress) external view returns (bool);
    function hasClaim(address _userAddress, uint256 _topic) external view returns (bool);
    function getInvestorCountry(address _userAddress) external view returns (uint16);
    function registerIdentity(address _userAddress, uint16 _country, uint256[] calldata _claims) external;
    function revokeIdentity(address _userAddress) external;
}

interface IModularCompliance {
    function canTransfer(address _from, address _to, uint256 _amount) external view returns (bool);
    function transferred(address _from, address _to, uint256 _amount) external;
}

/**
 * @title IdentityRegistry
 * @notice Production OnChainID Registry with granular claim topics & country tracking.
 */
contract IdentityRegistry is IIdentityRegistry {
    address public agent;
    
    struct IdentityRecord {
        bool exists;
        uint16 countryCode; // ISO-3166 Numeric
        mapping(uint256 => bool) claims;
    }

    mapping(address => IdentityRecord) private _identities;

    event IdentityRegistered(address indexed investor, uint16 country);
    event ClaimAdded(address indexed investor, uint256 topic);
    event IdentityRevoked(address indexed investor);

    modifier onlyAgent() {
        require(msg.sender == agent, "Only Agent Authority");
        _;
    }

    constructor() {
        agent = msg.sender;
    }

    function isVerified(address _userAddress) external view override returns (bool) {
        IdentityRecord storage record = _identities[_userAddress];
        return record.exists && record.claims[10101] && record.claims[10102];
    }

    function hasClaim(address _userAddress, uint256 _topic) external view override returns (bool) {
        return _identities[_userAddress].claims[_topic];
    }

    function getInvestorCountry(address _userAddress) external view override returns (uint16) {
        return _identities[_userAddress].countryCode;
    }

    function registerIdentity(address _userAddress, uint16 _country, uint256[] calldata _claims) external override onlyAgent {
        IdentityRecord storage record = _identities[_userAddress];
        record.exists = true;
        record.countryCode = _country;
        for (uint256 i = 0; i < _claims.length; i++) {
            record.claims[_claims[i]] = true;
            emit ClaimAdded(_userAddress, _claims[i]);
        }
        emit IdentityRegistered(_userAddress, _country);
    }

    function revokeIdentity(address _userAddress) external override onlyAgent {
        delete _identities[_userAddress];
        emit IdentityRevoked(_userAddress);
    }
}

/**
 * @title DignityGoldCompliance
 * @notice Modular Compliance Rule Engine (Reg D Lockups, Velocity, Country Caps)
 */
contract DignityGoldCompliance is IModularCompliance {
    address public agent;
    IIdentityRegistry public identityRegistry;

    mapping(address => uint256) public lockupExpiry;
    mapping(uint16 => bool) public sanctionedCountries;
    mapping(address => uint256) public dailyTransferred;
    mapping(address => uint256) public lastTransferDay;
    uint256 public constant DAILY_VELOCITY_LIMIT = 2500000 * 1e18; // 2.5M DIGau per day

    modifier onlyAgent() {
        require(msg.sender == agent, "Only Agent Authority");
        _;
    }

    constructor(address _identityRegistry) {
        agent = msg.sender;
        identityRegistry = IIdentityRegistry(_identityRegistry);
        // Sanctioned country test codes
        sanctionedCountries[408] = true; // DPRK
        sanctionedCountries[364] = true; // Iran
    }

    function setLockup(address _wallet, uint256 _durationSeconds) external onlyAgent {
        lockupExpiry[_wallet] = block.timestamp + _durationSeconds;
    }

    function canTransfer(address _from, address _to, uint256 _amount) external view override returns (bool) {
        if (_amount == 0) return false;
        
        // Exemption for initial issuance (minting from address(0))
        if (_from == address(0)) return true;

        // Rule 1: Reg D / Rule 144 Transfer Lockup
        if (block.timestamp < lockupExpiry[_from]) {
            return false;
        }

        // Rule 2: Country Sanction / Jurisdiction Check
        uint16 destCountry = identityRegistry.getInvestorCountry(_to);
        if (sanctionedCountries[destCountry]) {
            return false;
        }

        // Rule 3: Velocity Limit (24h Window)
        uint256 currentDay = block.timestamp / 1 days;
        uint256 spentToday = (lastTransferDay[_from] == currentDay) ? dailyTransferred[_from] : 0;
        if (spentToday + _amount > DAILY_VELOCITY_LIMIT) {
            return false;
        }

        return true;
    }

    function transferred(address _from, address, uint256 _amount) external override {
        if (_from != address(0)) {
            uint256 currentDay = block.timestamp / 1 days;
            if (lastTransferDay[_from] == currentDay) {
                dailyTransferred[_from] += _amount;
            } else {
                lastTransferDay[_from] = currentDay;
                dailyTransferred[_from] = _amount;
            }
        }
    }
}

/**
 * @title DignityGoldSecuritizedToken
 * @notice Production ERC-3643 Gold-Backed Security Token with Invariant Safeguards
 */
contract DignityGoldSecuritizedToken {
    string public name = "Dignity Gold Securitized Reserve";
    string public symbol = "DIGau";
    uint8 public constant decimals = 18;
    uint256 public totalSupply;

    address public owner;
    IIdentityRegistry public identityRegistry;
    IModularCompliance public compliance;

    string public constant enterpriseId = "69a0b54edd793f289161ec0c50cee070";
    string public vaultDepositoryRef = "BITGO-GOLD-VAULT-DIGAU-01";
    string public latestAssayReportHash;
    
    uint256 public maxOuncesAuthorized;
    uint256 public goldOuncesInCustody;
    bool public paused;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => bool) public frozenWallets;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event WalletFrozen(address indexed wallet, bool frozen);
    event SecurityHalt(bool isPaused);
    event ReserveAssayUpdated(string newHash, uint256 authorizedOunces);
    event SecuritizedTrancheMinted(address indexed to, uint256 tokens, uint256 ounces, string wireRef);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only Issuer Authority");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "ERC-3643: Trading paused by compliance");
        _;
    }

    constructor(
        address _identityRegistry,
        address _compliance,
        string memory _initialAssayHash,
        uint256 _initialAuthorizedOunces
    ) {
        owner = msg.sender;
        identityRegistry = IIdentityRegistry(_identityRegistry);
        compliance = IModularCompliance(_compliance);
        latestAssayReportHash = _initialAssayHash;
        maxOuncesAuthorized = _initialAuthorizedOunces;
    }

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
        require(identityRegistry.isVerified(_from), "ERC-3643: Sender KYC invalid");
        require(identityRegistry.isVerified(_to), "ERC-3643: Recipient KYC invalid");
        require(compliance.canTransfer(_from, _to, _amount), "ERC-3643: Blocked by modular compliance");
        require(balanceOf[_from] >= _amount, "ERC-3643: Insufficient DIGau balance");

        balanceOf[_from] -= _amount;
        balanceOf[_to] += _amount;
        compliance.transferred(_from, _to, _amount);

        emit Transfer(_from, _to, _amount);
    }

    function mint(
        address _to,
        uint256 _amountTokens,
        uint256 _ouncesAllocated,
        string memory _wireRef
    ) external onlyOwner whenNotPaused {
        require(identityRegistry.isVerified(_to), "ERC-3643: Target investor failed KYC");
        require(!frozenWallets[_to], "ERC-3643: Target wallet frozen");
        require(goldOuncesInCustody + _ouncesAllocated <= maxOuncesAuthorized, "ERC-3643: Exceeds audited physical gold reserves");

        totalSupply += _amountTokens;
        balanceOf[_to] += _amountTokens;
        goldOuncesInCustody += _ouncesAllocated;

        emit Transfer(address(0), _to, _amountTokens);
        emit SecuritizedTrancheMinted(_to, _amountTokens, _ouncesAllocated, _wireRef);
    }

    function setWalletFrozen(address _wallet, bool _frozen) external onlyOwner {
        frozenWallets[_wallet] = _frozen;
        emit WalletFrozen(_wallet, _frozen);
    }

    function setPaused(bool _paused) external onlyOwner {
        paused = _paused;
        emit SecurityHalt(_paused);
    }

    function updateAssayAudit(string memory _newHash, uint256 _newAuthorizedOunces) external onlyOwner {
        latestAssayReportHash = _newHash;
        maxOuncesAuthorized = _newAuthorizedOunces;
        emit ReserveAssayUpdated(_newHash, _newAuthorizedOunces);
    }
}
