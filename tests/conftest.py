"""
Shared fixtures for the uniswap-mcp-server test suite.

All blockchain/RPC calls are mocked so tests run fully offline.
"""

import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# Environment helpers

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Remove any real .env values so tests control every env variable."""
    monkeypatch.delenv("RPC_URL", raising=False)
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.delenv("DEFAULT_FEE_TIER", raising=False)
    monkeypatch.delenv("DEFAULT_SLIPPAGE_BPS", raising=False)


@pytest.fixture
def rpc_url():
    return "http://localhost:8545"


@pytest.fixture
def private_key():
    # Deterministic test key — never use for real funds.
    return "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


# Mock Web3 instance

@pytest.fixture
def mock_web3():
    """Return a fully-mocked Web3 instance that never touches the network."""
    w3 = MagicMock()
    w3.eth.chain_id = 1
    w3.eth.block_number = 20_000_000
    w3.is_connected.return_value = True
    w3.eth.is_connected.return_value = True
    w3.to_checksum_address.side_effect = lambda addr: addr  # pass-through
    w3.middleware_onion = MagicMock()
    return w3


# Common token/pool addresses (checksum-style for assertions)

WETH  = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC  = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDT  = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
DAI   = "0x6B175474E89094C44Da98b954EedeAC495271d0F"

POOL_V3 = "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"  # USDC/WETH 0.05%
PAIR_V2 = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"  # USDC/WETH V2

ZERO_ADDR = "0x0000000000000000000000000000000000000000"
