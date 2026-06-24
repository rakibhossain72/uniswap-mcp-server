"""Uniswap V3 Factory contract wrapper."""

from web3 import Web3

from ..abis import V3_FACTORY_ABI
from .base import BaseContract


class V3Factory(BaseContract):
    """Uniswap V3 Factory contract wrapper."""

    def __init__(self, web3: Web3, address: str):
        super().__init__(web3, address, V3_FACTORY_ABI())

    def get_pool(self, token0: str, token1: str, fee: int) -> str:
        """Get the pool address for tokens and fee tier."""
        token0 = Web3.to_checksum_address(token0)
        token1 = Web3.to_checksum_address(token1)
        return self.contract.functions.getPool(token0, token1, fee).call()

    def fee_amount_tick_spacing(self, fee: int) -> int:
        """Get the tick spacing for a fee tier."""
        return self.contract.functions.feeAmountTickSpacing(fee).call()

    def owner(self) -> str:
        """Get the owner address."""
        return self.contract.functions.owner().call()
