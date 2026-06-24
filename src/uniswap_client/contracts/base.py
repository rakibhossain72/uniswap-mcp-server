"""Base contract class for all contract wrappers."""

from typing import Optional
from web3 import Web3
from web3.types import TxReceipt


class BaseContract:
    """Base class for all contract wrappers."""
    
    def __init__(self, web3: Web3, address: str, abi: list):
        self.web3 = web3
        self.address = Web3.to_checksum_address(address)
        self.contract = web3.eth.contract(address=self.address, abi=abi)

    def _checksum(self, address: str) -> str:
        """Convert address to checksum format."""
        return self.web3.to_checksum_address(address)