"""
Tests for src/resources/ — MCP resource functions.

  - get_protocol_addresses  (protocol://addresses)
  - get_network_status      (network://status)

Patching strategy: resource modules do `from server import mcp, get_client`
at import time, so we patch the name in each module's own namespace.

Async strategy: get_network_status uses asyncio.to_thread; we use
asyncio.run() to create a fresh event loop per test (Python 3.14 compatible).
"""

import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch

from tests.conftest import WETH, USDC


def _make_client_mock(chain_id=1):
    client = MagicMock()
    client.chain_id = chain_id
    client.w3 = MagicMock()
    client.w3.eth.block_number = 20_000_000
    client.w3.is_connected.return_value = True
    return client


# get_protocol_addresses

class TestGetProtocolAddresses:
    def _call(self, chain_id=1):
        mock_client = _make_client_mock(chain_id=chain_id)
        with patch("src.resources.addresses.get_client", return_value=mock_client):
            from src.resources.addresses import get_protocol_addresses
            return json.loads(get_protocol_addresses())

    def test_returns_json_string(self):
        mock_client = _make_client_mock(chain_id=1)
        with patch("src.resources.addresses.get_client", return_value=mock_client):
            from src.resources.addresses import get_protocol_addresses
            raw = get_protocol_addresses()
        assert isinstance(raw, str)
        assert isinstance(json.loads(raw), dict)

    def test_contains_chain_id(self):
        assert self._call(chain_id=1)["chain_id"] == 1

    def test_contains_chain_name_for_mainnet(self):
        assert self._call(chain_id=1)["chain_name"] == "MAINNET"

    def test_contains_chain_name_for_polygon(self):
        assert self._call(chain_id=137)["chain_name"] == "POLYGON"

    def test_contains_protocol_address_fields(self):
        data = self._call(chain_id=1)
        for field in ("v2_factory", "v3_factory", "v3_quoter", "v3_router", "weth", "usdc", "usdt"):
            assert field in data, f"Expected field '{field}' in address resource"

    def test_weth_address_on_mainnet(self):
        assert self._call(chain_id=1)["weth"] == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

    def test_usdc_address_on_mainnet(self):
        assert self._call(chain_id=1)["usdc"] == "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

    def test_returns_error_json_for_unsupported_chain(self):
        assert "error" in self._call(chain_id=9999)

    def test_polygon_has_different_weth_than_mainnet(self):
        assert self._call(chain_id=1)["weth"] != self._call(chain_id=137)["weth"]

    def test_output_is_pretty_printed_json(self):
        mock_client = _make_client_mock(chain_id=1)
        with patch("src.resources.addresses.get_client", return_value=mock_client):
            from src.resources.addresses import get_protocol_addresses
            assert "\n" in get_protocol_addresses()

    def test_optimism_chain_name(self):
        assert self._call(chain_id=10)["chain_name"] == "OPTIMISM"

    def test_arbitrum_chain_name(self):
        assert self._call(chain_id=42161)["chain_name"] == "ARBITRUM"


# get_network_status

class TestGetNetworkStatus:
    def _call(self, chain_id=1, block_number=20_000_000, connected=True):
        mock_client = _make_client_mock(chain_id=chain_id)
        mock_client.w3.eth.block_number = block_number
        mock_client.w3.is_connected.return_value = connected
        with patch("src.resources.network.get_client", return_value=mock_client):
            from src.resources.network import get_network_status
            return json.loads(asyncio.run(get_network_status()))

    def test_returns_dict(self):
        assert isinstance(self._call(), dict)

    def test_contains_chain_id(self):
        assert self._call(chain_id=1)["chain_id"] == 1

    def test_contains_latest_block(self):
        assert self._call(block_number=19_999_999)["latest_block"] == 19_999_999

    def test_connected_true_when_node_reachable(self):
        assert self._call(connected=True)["connected"] is True

    def test_connected_false_when_node_unreachable(self):
        assert self._call(connected=False)["connected"] is False

    def test_chain_id_137_polygon(self):
        assert self._call(chain_id=137)["chain_id"] == 137

    def test_output_is_pretty_printed_json(self):
        mock_client = _make_client_mock(chain_id=1)
        with patch("src.resources.network.get_client", return_value=mock_client):
            from src.resources.network import get_network_status
            assert "\n" in asyncio.run(get_network_status())
