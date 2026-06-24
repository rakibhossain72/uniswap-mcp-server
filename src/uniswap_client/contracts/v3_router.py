"""Uniswap V3 Router contract wrapper."""

from web3 import Web3

from ..abis import V3_ROUTER_ABI
from .base import BaseContract


class V3Router(BaseContract):
    """Uniswap V3 Router contract wrapper."""

    def __init__(self, web3: Web3, address: str):
        super().__init__(web3, address, V3_ROUTER_ABI())

    def exact_input_single(self, params: dict):
        """Swap exact input for a single pool."""
        return self.contract.functions.exactInputSingle(params)

    def exact_input(self, params: dict):
        """Swap exact input for a multi-hop swap."""
        return self.contract.functions.exactInput(params)

    def exact_output_single(self, params: dict):
        """Swap exact output for a single pool."""
        return self.contract.functions.exactOutputSingle(params)

    def exact_output(self, params: dict):
        """Swap exact output for a multi-hop swap."""
        return self.contract.functions.exactOutput(params)

    def multicall(self, data: list):
        """Execute multiple calls in one transaction."""
        return self.contract.functions.multicall(data)

    def unwrap_weth(self, amount_min: int, recipient: str):
        """Unwrap WETH to ETH."""
        recipient = Web3.to_checksum_address(recipient)
        return self.contract.functions.unwrapWETH9(amount_min, recipient)

    def refund_eth(self):
        """Refund ETH."""
        return self.contract.functions.refundETH()

    def sweep_token(self, token: str, amount_min: int, recipient: str):
        """Sweep tokens."""
        token = Web3.to_checksum_address(token)
        recipient = Web3.to_checksum_address(recipient)
        return self.contract.functions.sweepToken(token, amount_min, recipient)
