"""Uniswap V3 Pool contract wrapper."""

from web3 import Web3

from ..abis import V3_POOL_ABI
from .base import BaseContract


class V3Pool(BaseContract):
    """Uniswap V3 Pool contract wrapper."""

    def __init__(self, web3: Web3, address: str):
        super().__init__(web3, address, V3_POOL_ABI())

    def slot0(self) -> tuple:
        """Get the slot0 data (sqrtPriceX96, tick, etc.)."""
        return self.contract.functions.slot0().call()

    def liquidity(self) -> int:
        """Get the current liquidity."""
        return self.contract.functions.liquidity().call()

    def fee(self) -> int:
        """Get the fee tier."""
        return self.contract.functions.fee().call()

    def token0(self) -> str:
        """Get the address of token0."""
        return self.contract.functions.token0().call()

    def token1(self) -> str:
        """Get the address of token1."""
        return self.contract.functions.token1().call()

    def tick_spacing(self) -> int:
        """Get the tick spacing."""
        return self.contract.functions.tickSpacing().call()

    def max_liquidity_per_tick(self) -> int:
        """Get the max liquidity per tick."""
        return self.contract.functions.maxLiquidityPerTick().call()

    def ticks(self, tick: int) -> tuple:
        """Get tick data for a specific tick."""
        return self.contract.functions.ticks(tick).call()

    def observations(self, index: int) -> tuple:
        """Get observation data at index."""
        return self.contract.functions.observations(index).call()

    def positions(self, owner: str, tick_lower: int, tick_upper: int) -> tuple:
        """Get position data."""
        owner = Web3.to_checksum_address(owner)
        return self.contract.functions.positions(owner, tick_lower, tick_upper).call()

    def snapshot_cumulatives_inside(self, tick_lower: int, tick_upper: int) -> tuple:
        """Get cumulative data inside a tick range."""
        return self.contract.functions.snapshotCumulativesInside(
            tick_lower, tick_upper
        ).call()

    def observe(self, seconds_ago: list) -> tuple:
        """Get observations from the past."""
        return self.contract.functions.observe(seconds_ago).call()

    def increase_observation_cardinality_next(self, cardinality_next: int):
        """Increase the observation cardinality."""
        return self.contract.functions.increaseObservationCardinalityNext(
            cardinality_next
        )

    def mint(
        self, recipient: str, tick_lower: int, tick_upper: int, amount: int, data: bytes
    ):
        """Mint liquidity."""
        recipient = Web3.to_checksum_address(recipient)
        return self.contract.functions.mint(
            recipient, tick_lower, tick_upper, amount, data
        )

    def collect(
        self,
        recipient: str,
        tick_lower: int,
        tick_upper: int,
        amount0: int,
        amount1: int,
    ):
        """Collect fees."""
        recipient = Web3.to_checksum_address(recipient)
        return self.contract.functions.collect(
            recipient, tick_lower, tick_upper, amount0, amount1
        )

    def burn(self, tick_lower: int, tick_upper: int, amount: int):
        """Burn liquidity."""
        return self.contract.functions.burn(tick_lower, tick_upper, amount)

    def swap(
        self,
        recipient: str,
        zero_for_one: bool,
        amount_specified: int,
        sqrt_price_limit_x96: int,
        data: bytes,
    ):
        """Execute a swap."""
        recipient = Web3.to_checksum_address(recipient)
        return self.contract.functions.swap(
            recipient, zero_for_one, amount_specified, sqrt_price_limit_x96, data
        )

    def flash(self, recipient: str, amount0: int, amount1: int, data: bytes):
        """Execute a flash loan."""
        recipient = Web3.to_checksum_address(recipient)
        return self.contract.functions.flash(recipient, amount0, amount1, data)

    def fee_growth_global0_x128(self) -> int:
        """Get global fee growth of token0."""
        return self.contract.functions.feeGrowthGlobal0X128().call()

    def fee_growth_global1_x128(self) -> int:
        """Get global fee growth of token1."""
        return self.contract.functions.feeGrowthGlobal1X128().call()

    def protocol_fees(self) -> tuple:
        """Get protocol fees."""
        return self.contract.functions.protocolFees().call()
