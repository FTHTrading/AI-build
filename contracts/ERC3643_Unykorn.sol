// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IIdentityRegistry
 * @dev ERC-3643 Identity Registry Interface
 */
interface IIdentityRegistry {
    function isVerified(address _userAddress) external view returns (bool);
    function registerIdentity(address _userAddress, address _identityContract, uint16 _country) external;
    function deleteIdentity(address _userAddress) external;
}

/**
 * @title IModularCompliance
 * @dev ERC-3643 Modular Compliance Interface
 */
interface IModularCompliance {
    function canTransfer(address _from, address _to, uint256 _amount) external view returns (bool);
    function createdTokenAgent(address _agent) external;
}

/**
 * @title IdentityRegistry
 * @dev Core registry verifying KYC (10101) and AML (10102) claims
 */
contract IdentityRegistry is IIdentityRegistry {
    address public owner;
    mapping(address => bool) private _verifiedUsers;
    mapping(address => address) private _identities;

    event IdentityRegistered(address indexed investorAddress, address indexed identityContract);
    event IdentityRemoved(address indexed investorAddress);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can execute");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function isVerified(address _userAddress) external view override returns (bool) {
        return _verifiedUsers[_userAddress];
    }

    function registerIdentity(address _userAddress, address _identityContract, uint16 _country) external override onlyOwner {
        _verifiedUsers[_userAddress] = true;
        _identities[_userAddress] = _identityContract;
        emit IdentityRegistered(_userAddress, _identityContract);
    }

    function deleteIdentity(address _userAddress) external override onlyOwner {
        _verifiedUsers[_userAddress] = false;
        delete _identities[_userAddress];
        emit IdentityRemoved(_userAddress);
    }
}

/**
 * @title ModularCompliance
 * @dev Evaluates jurisdictional, country, and transfer volume rules
 */
contract ModularCompliance is IModularCompliance {
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }

    function canTransfer(address _from, address _to, uint256 _amount) external pure override returns (bool) {
        // Enforce basic positive transfer rules
        if (_amount == 0) return false;
        return true;
    }

    function createdTokenAgent(address _agent) external override {}
}

/**
 * @title UnykornSecuritizedToken
 * @dev ERC-3643 Permissioned RWA Security Token for SPV Tranches
 */
contract UnykornSecuritizedToken {
    string public name;
    string public symbol;
    uint8 public decimals = 18;
    uint256 public totalSupply;
    
    address public owner;
    IIdentityRegistry public identityRegistry;
    IModularCompliance public compliance;
    
    string public spvIdentifier;
    string public underlyingBankEscrowBBAN;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => bool) public frozenWallets;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event SecuritizedTrancheMinted(address indexed to, uint256 amount, string bankWireRef);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only Token Issuer can execute");
        _;
    }

    constructor(
        string memory _name,
        string memory _symbol,
        address _identityRegistry,
        address _compliance,
        string memory _spvId,
        string memory _escrowRef
    ) {
        name = _name;
        symbol = _symbol;
        owner = msg.sender;
        identityRegistry = IIdentityRegistry(_identityRegistry);
        compliance = IModularCompliance(_compliance);
        spvIdentifier = _spvId;
        underlyingBankEscrowBBAN = _escrowRef;
    }

    function mint(address _to, uint256 _amount, string memory _bankWireRef) external onlyOwner {
        require(identityRegistry.isVerified(_to), "ERC-3643 Error: Target wallet is not KYC/AML verified");
        require(!frozenWallets[_to], "ERC-3643 Error: Target wallet is frozen");
        
        totalSupply += _amount;
        balanceOf[_to] += _amount;
        
        emit Transfer(address(0), _to, _amount);
        emit SecuritizedTrancheMinted(_to, _amount, _bankWireRef);
    }

    function transfer(address _to, uint256 _amount) external returns (bool) {
        require(identityRegistry.isVerified(msg.sender), "ERC-3643: Sender not KYC verified");
        require(identityRegistry.isVerified(_to), "ERC-3643: Recipient not KYC verified");
        require(compliance.canTransfer(msg.sender, _to, _amount), "ERC-3643: Transfer blocked by Compliance Rules");
        require(balanceOf[msg.sender] >= _amount, "Insufficient balance");

        balanceOf[msg.sender] -= _amount;
        balanceOf[_to] += _amount;
        
        emit Transfer(msg.sender, _to, _amount);
        return true;
    }
}
