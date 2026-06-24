"""ERC20 token contract wrapper."""

from typing import Dict, Any
from web3 import Web3

from ..abis import ERC20_ABI
from .base import BaseContract


class ERC20(BaseContract):
    """ERC20 token helper class for interacting with ERC20 tokens."""

    def __init__(self, web3: Web3):
        # ERC20 doesn't have a fixed address, will be set per call
        self.web3 = web3
        self.abi = ERC20_ABI()

    def _get_contract(self, token_contract: str):
        """Get the contract instance for a token."""
        token_contract = Web3.to_checksum_address(token_contract)
        return self.web3.eth.contract(address=token_contract, abi=self.abi)

    def decimal(self, token_contract: str) -> int:
        """Get the number of decimals the token uses."""
        token_contract = Web3.to_checksum_address(token_contract)
        return self._get_contract(token_contract).functions.decimals().call()

    def symbol(self, token_contract: str) -> str:
        """Get the token symbol."""
        token_contract = Web3.to_checksum_address(token_contract)
        return self._get_contract(token_contract).functions.symbol().call()

    def name(self, token_contract: str) -> str:
        """Get the token name."""
        token_contract = Web3.to_checksum_address(token_contract)
        return self._get_contract(token_contract).functions.name().call()

    def total_supply(self, token_contract: str) -> int:
        """Get the total token supply."""
        token_contract = Web3.to_checksum_address(token_contract)
        return self._get_contract(token_contract).functions.totalSupply().call()

    def balance_of(self, token_contract: str, account: str) -> int:
        """Get the token balance of a specific account."""
        token_contract = Web3.to_checksum_address(token_contract)
        account = Web3.to_checksum_address(account)
        return self._get_contract(token_contract).functions.balanceOf(account).call()

    def allowance(self, token_contract: str, owner: str, spender: str) -> int:
        """Get the amount of tokens that spender is allowed to spend on behalf of owner."""
        token_contract = Web3.to_checksum_address(token_contract)
        owner = Web3.to_checksum_address(owner)
        spender = Web3.to_checksum_address(spender)
        return (
            self._get_contract(token_contract)
            .functions.allowance(owner, spender)
            .call()
        )

    def approve(self, token_contract: str, spender: str, amount: int):
        """Approve spender to spend tokens on behalf of the caller."""
        token_contract = Web3.to_checksum_address(token_contract)
        spender = Web3.to_checksum_address(spender)
        contract = self._get_contract(token_contract)
        return contract.functions.approve(spender, amount)

    def is_contract(self, address: str) -> bool:
        """Check if an address is a contract."""
        address = Web3.to_checksum_address(address)
        code = self.web3.eth.get_code(address)
        return len(code) > 0

    def format_amount(self, token_contract: str, amount: int) -> float:
        """Format a raw amount to a human-readable decimal format."""
        decimals = self.decimal(token_contract)
        return amount / (10**decimals)

    def parse_amount(self, token_contract: str, amount: float) -> int:
        """Parse a human-readable amount to raw token amount."""
        decimals = self.decimal(token_contract)
        return int(amount * (10**decimals))
