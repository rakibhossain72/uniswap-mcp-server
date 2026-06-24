"""Uniswap V2 Pair contract wrapper."""

from web3 import Web3

from ..abis import V2_PAIR_ABI
from .base import BaseContract


class V2Pair(BaseContract):
    """Uniswap V2 Pair contract wrapper."""

    def __init__(self, web3: Web3, address: str):
        super().__init__(web3, address, V2_PAIR_ABI())

    def get_reserves(self) -> tuple:
        """Get the reserves of the pair."""
        return self.contract.functions.getReserves().call()

    def token0(self) -> str:
        """Get the address of token0."""
        return self.contract.functions.token0().call()

    def token1(self) -> str:
        """Get the address of token1."""
        return self.contract.functions.token1().call()

    def total_supply(self) -> int:
        """Get the total supply of LP tokens."""
        return self.contract.functions.totalSupply().call()

    def balance_of(self, account: str) -> int:
        """Get LP token balance of an account."""
        account = Web3.to_checksum_address(account)
        return self.contract.functions.balanceOf(account).call()

    def price0_cumulative_last(self) -> int:
        """Get cumulative price of token0."""
        return self.contract.functions.price0CumulativeLast().call()

    def price1_cumulative_last(self) -> int:
        """Get cumulative price of token1."""
        return self.contract.functions.price1CumulativeLast().call()

    def k_last(self) -> int:
        """Get the last K value."""
        return self.contract.functions.kLast().call()

    def factory(self) -> str:
        """Get the factory address."""
        return self.contract.functions.factory().call()

    def get_amount_out(self, amount_in: int, reserve_in: int, reserve_out: int) -> int:
        """Calculate amount out for a given amount in."""
        return self.contract.functions.getAmountOut(
            amount_in, reserve_in, reserve_out
        ).call()

    def get_amount_in(self, amount_out: int, reserve_in: int, reserve_out: int) -> int:
        """Calculate amount in for a given amount out."""
        return self.contract.functions.getAmountIn(
            amount_out, reserve_in, reserve_out
        ).call()
