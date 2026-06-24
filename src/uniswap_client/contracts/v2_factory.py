"""Uniswap V2 Factory contract wrapper."""

from web3 import Web3

from ..abis import V2_FACTORY_ABI
from .base import BaseContract


class V2Factory(BaseContract):
    """Uniswap V2 Factory contract wrapper."""

    def __init__(self, web3: Web3, address: str):
        super().__init__(web3, address, V2_FACTORY_ABI())

    def get_pair(self, token0: str, token1: str) -> str:
        """Get the pair address for two tokens."""
        token0 = Web3.to_checksum_address(token0)
        token1 = Web3.to_checksum_address(token1)
        return self.contract.functions.getPair(token0, token1).call()

    def all_pairs(self, index: int) -> str:
        """Get pair address at index."""
        return self.contract.functions.allPairs(index).call()

    def all_pairs_length(self) -> int:
        """Get total number of pairs."""
        return self.contract.functions.allPairsLength().call()

    def fee_to(self) -> str:
        """Get the fee recipient address."""
        return self.contract.functions.feeTo().call()

    def fee_to_setter(self) -> str:
        """Get the fee setter address."""
        return self.contract.functions.feeToSetter().call()
