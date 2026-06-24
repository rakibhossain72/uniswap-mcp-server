"""Uniswap V3 Quoter contract wrapper."""

from web3 import Web3

from ..abis import V3_QUOTER_ABI
from .base import BaseContract


class V3Quoter(BaseContract):
    """Uniswap V3 Quoter contract wrapper."""

    def __init__(self, web3: Web3, address: str):
        super().__init__(web3, address, V3_QUOTER_ABI())

    def quote_exact_input_single(
        self,
        token_in: str,
        token_out: str,
        fee: int,
        amount_in: int,
        sqrt_price_limit_x96: int = 0,
    ) -> int:
        """Quote exact input for a single pool."""
        token_in = Web3.to_checksum_address(token_in)
        token_out = Web3.to_checksum_address(token_out)
        return self.contract.functions.quoteExactInputSingle(
            token_in, token_out, fee, amount_in, sqrt_price_limit_x96
        ).call()

    def quote_exact_input(self, path: list, amount_in: int) -> int:
        """Quote exact input for a multi-hop swap."""
        return self.contract.functions.quoteExactInput(path, amount_in).call()

    def quote_exact_output_single(
        self,
        token_in: str,
        token_out: str,
        fee: int,
        amount_out: int,
        sqrt_price_limit_x96: int = 0,
    ) -> int:
        """Quote exact output for a single pool."""
        token_in = Web3.to_checksum_address(token_in)
        token_out = Web3.to_checksum_address(token_out)
        return self.contract.functions.quoteExactOutputSingle(
            token_in, token_out, fee, amount_out, sqrt_price_limit_x96
        ).call()

    def quote_exact_output(self, path: list, amount_out: int) -> int:
        """Quote exact output for a multi-hop swap."""
        return self.contract.functions.quoteExactOutput(path, amount_out).call()
