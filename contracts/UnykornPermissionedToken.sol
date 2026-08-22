// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IIdentityRegistry} from "./IIdentityRegistry.sol";
import {ICompliance} from "./ICompliance.sol";

contract UnykornPermissionedToken is IERC20, AccessControl {
    bytes32 public constant AGENT_ROLE = keccak256("AGENT_ROLE");
    bytes32 public constant COMPLIANCE_ADMIN_ROLE = keccak256("COMPLIANCE_ADMIN_ROLE");

    string private _name;
    string private _symbol;
    uint8 private immutable _decimals;
    uint256 private _totalSupply;

    IIdentityRegistry public identityRegistry;
    ICompliance public compliance;
    bool public paused;

    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;
    mapping(address => bool) private _frozen;

    // Events
    event UpdatedIdentityRegistry(address indexed newIdentityRegistry);
    event UpdatedCompliance(address indexed newCompliance);
    event AddressFrozen(address indexed userAddress, bool indexed isFrozen);
    event TokensPaused(bool isPaused);
    event TokensForcedRecovery(address indexed lostWallet, address indexed newWallet, uint256 amount);

    // Custom Errors
    error TransferNotAllowed();
    error SenderNotVerified();
    error RecipientNotVerified();
    error WalletIsFrozen(address wallet);
    error TokenIsPaused();
    error InsufficientBalance();
    error InsufficientAllowance();

    constructor(
        string memory name_,
        string memory symbol_,
        uint8 decimals_,
        address admin_,
        address identityRegistry_,
        address compliance_
    ) {
        _name = name_;
        _symbol = symbol_;
        _decimals = decimals_;

        _grantRole(DEFAULT_ADMIN_ROLE, admin_);
        _grantRole(AGENT_ROLE, admin_);
        _grantRole(COMPLIANCE_ADMIN_ROLE, admin_);

        identityRegistry = IIdentityRegistry(identityRegistry_);
        compliance = ICompliance(compliance_);
    }

    function name() external view returns (string memory) { return _name; }
    function symbol() external view returns (string memory) { return _symbol; }
    function decimals() external view returns (uint8) { return _decimals; }
    function totalSupply() external view override returns (uint256) { return _totalSupply; }
    function balanceOf(address account) external view override returns (uint256) { return _balances[account]; }

    function allowance(address owner, address spender) external view override returns (uint256) {
        return _allowances[owner][spender];
    }

    function setIdentityRegistry(address newIdentityRegistry) external onlyRole(COMPLIANCE_ADMIN_ROLE) {
        identityRegistry = IIdentityRegistry(newIdentityRegistry);
        emit UpdatedIdentityRegistry(newIdentityRegistry);
    }

    function setCompliance(address newCompliance) external onlyRole(COMPLIANCE_ADMIN_ROLE) {
        compliance = ICompliance(newCompliance);
        emit UpdatedCompliance(newCompliance);
    }

    function setAddressFrozen(address wallet, bool freezeState) external onlyRole(AGENT_ROLE) {
        _frozen[wallet] = freezeState;
        emit AddressFrozen(wallet, freezeState);
    }

    function setPause(bool pauseState) external onlyRole(AGENT_ROLE) {
        paused = pauseState;
        emit TokensPaused(pauseState);
    }

    function isFrozen(address wallet) external view returns (bool) {
        return _frozen[wallet];
    }

    function approve(address spender, uint256 amount) external override returns (bool) {
        _approve(msg.sender, spender, amount);
        return true;
    }

    function transfer(address to, uint256 amount) external override returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external override returns (bool) {
        uint256 currentAllowance = _allowances[from][msg.sender];
        if (currentAllowance < amount) revert InsufficientAllowance();
        
        unchecked {
            _approve(from, msg.sender, currentAllowance - amount);
        }
        _transfer(from, to, amount);
        return true;
    }

    function mint(address to, uint256 amount) external onlyRole(AGENT_ROLE) {
        if (!identityRegistry.isVerified(to)) revert RecipientNotVerified();
        if (_frozen[to]) revert WalletIsFrozen(to);

        _totalSupply += amount;
        unchecked {
            _balances[to] += amount;
        }

        if (address(compliance) != address(0)) {
            compliance.created(to, amount);
        }

        emit Transfer(address(0), to, amount);
    }

    function burn(address from, uint256 amount) external onlyRole(AGENT_ROLE) {
        if (_balances[from] < amount) revert InsufficientBalance();

        unchecked {
            _balances[from] -= amount;
            _totalSupply -= amount;
        }

        if (address(compliance) != address(0)) {
            compliance.destroyed(from, amount);
        }

        emit Transfer(from, address(0), amount);
    }

    function forceRecovery(address lostWallet, address newWallet) external onlyRole(AGENT_ROLE) {
        if (!identityRegistry.isVerified(newWallet)) revert RecipientNotVerified();
        uint256 lostBalance = _balances[lostWallet];
        if (lostBalance == 0) revert InsufficientBalance();

        _balances[lostWallet] = 0;
        _balances[newWallet] += lostBalance;

        emit TokensForcedRecovery(lostWallet, newWallet, lostBalance);
        emit Transfer(lostWallet, newWallet, lostBalance);
    }

    function _transfer(address from, address to, uint256 amount) internal {
        if (paused) revert TokenIsPaused();
        if (_frozen[from]) revert WalletIsFrozen(from);
        if (_frozen[to]) revert WalletIsFrozen(to);
        if (!identityRegistry.isVerified(from)) revert SenderNotVerified();
        if (!identityRegistry.isVerified(to)) revert RecipientNotVerified();
        if (_balances[from] < amount) revert InsufficientBalance();

        if (address(compliance) != address(0)) {
            if (!compliance.canTransfer(from, to, amount)) revert TransferNotAllowed();
            compliance.transferred(from, to, amount);
        }

        unchecked {
            _balances[from] -= amount;
            _balances[to] += amount;
        }

        emit Transfer(from, to, amount);
    }

    function _approve(address owner, address spender, uint256 amount) internal {
        _allowances[owner][spender] = amount;
        emit Approval(owner, spender, amount);
    }
}
