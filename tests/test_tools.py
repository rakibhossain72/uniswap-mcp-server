"""
Tests for src/tools/ — MCP tool functions.

Patching strategy: each tool module does `from server import mcp, get_client`,
binding `get_client` into its own namespace.  We patch it there, e.g.
`src.tools.prices.get_client`, not `server.get_client`.

Async strategy: tools are async coroutines using asyncio.to_thread.
We use asyncio.run() for a fresh event loop per call (Python 3.14 compatible).
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch
from web3 import Web3

from tests.conftest import WETH, USDC, USDT, POOL_V3, PAIR_V2, ZERO_ADDR


def _make_client_mock(chain_id=1):
    client = MagicMock()
    client.chain_id = chain_id
    client.erc20    = MagicMock()
    return client


# get_token_price

class TestGetTokenPriceTool:
    def test_returns_price_from_client(self):
        mock_client = _make_client_mock()
        mock_client.get_token_price.return_value = {
            "token": "WETH", "address": WETH, "price_usd": 3000.0,
            "quote_token": "USDC", "fee_tier": 500, "pool_address": POOL_V3, "chain_id": 1,
        }
        with patch("src.tools.prices.get_client", return_value=mock_client):
            from src.tools.prices import get_token_price
            result = asyncio.run(get_token_price(token_address=WETH))

        assert result["price_usd"] == 3000.0
        mock_client.get_token_price.assert_called_once_with(token_address=WETH, chain_id=1)

    def test_passes_chain_id_from_client(self):
        mock_client = _make_client_mock(chain_id=137)
        mock_client.get_token_price.return_value = {"price_usd": 1.0}

        with patch("src.tools.prices.get_client", return_value=mock_client):
            from src.tools.prices import get_token_price
            asyncio.run(get_token_price(token_address=USDC))

        assert mock_client.get_token_price.call_args[1]["chain_id"] == 137

    def test_returns_error_dict_when_no_pool(self):
        mock_client = _make_client_mock()
        mock_client.get_token_price.return_value = {"error": "No V3 pool found"}

        with patch("src.tools.prices.get_client", return_value=mock_client):
            from src.tools.prices import get_token_price
            assert "error" in asyncio.run(get_token_price(token_address=WETH))


# get_v3_pool

class TestGetV3PoolTool:
    def test_returns_pool_data(self):
        mock_client = _make_client_mock()
        mock_client.get_v3_pool.return_value = {
            "pool_address": POOL_V3, "version": "v3", "fee_tier": 3000,
            "token0": {"symbol": "USDC"}, "token1": {"symbol": "WETH"},
        }
        with patch("src.tools.pools.get_client", return_value=mock_client):
            from src.tools.pools import get_v3_pool
            result = asyncio.run(get_v3_pool(token0=USDC, token1=WETH, fee=3000))

        assert result["pool_address"] == POOL_V3
        mock_client.get_v3_pool.assert_called_once_with(token0=USDC, token1=WETH, fee=3000, chain_id=1)

    def test_default_fee_tier_is_3000(self):
        mock_client = _make_client_mock()
        mock_client.get_v3_pool.return_value = {}
        with patch("src.tools.pools.get_client", return_value=mock_client):
            from src.tools.pools import get_v3_pool
            asyncio.run(get_v3_pool(token0=USDC, token1=WETH))
        assert mock_client.get_v3_pool.call_args[1]["fee"] == 3000

    def test_returns_error_dict_when_pool_not_found(self):
        mock_client = _make_client_mock()
        mock_client.get_v3_pool.return_value = {"error": "No V3 pool found for tokens with fee 3000"}
        with patch("src.tools.pools.get_client", return_value=mock_client):
            from src.tools.pools import get_v3_pool
            assert "error" in asyncio.run(get_v3_pool(token0=USDC, token1=USDT, fee=3000))

    def test_passes_chain_id_from_client(self):
        mock_client = _make_client_mock(chain_id=10)
        mock_client.get_v3_pool.return_value = {}
        with patch("src.tools.pools.get_client", return_value=mock_client):
            from src.tools.pools import get_v3_pool
            asyncio.run(get_v3_pool(token0=USDC, token1=WETH))
        assert mock_client.get_v3_pool.call_args[1]["chain_id"] == 10


# get_v2_pair

class TestGetV2PairTool:
    def test_returns_pair_data(self):
        mock_client = _make_client_mock()
        mock_client.get_v2_pair.return_value = {
            "pair_address": PAIR_V2, "version": "v2",
            "token0": {"symbol": "USDC"}, "token1": {"symbol": "WETH"},
        }
        with patch("src.tools.pools.get_client", return_value=mock_client):
            from src.tools.pools import get_v2_pair
            result = asyncio.run(get_v2_pair(token0=USDC, token1=WETH))

        assert result["pair_address"] == PAIR_V2
        mock_client.get_v2_pair.assert_called_once_with(token0=USDC, token1=WETH, chain_id=1)

    def test_returns_error_when_pair_missing(self):
        mock_client = _make_client_mock()
        mock_client.get_v2_pair.return_value = {"error": "No V2 pair found for these tokens"}
        with patch("src.tools.pools.get_client", return_value=mock_client):
            from src.tools.pools import get_v2_pair
            assert "error" in asyncio.run(get_v2_pair(token0=USDC, token1=USDT))


# get_pool_by_address

class TestGetPoolByAddressTool:
    def test_returns_pool_by_address(self):
        mock_client = _make_client_mock()
        mock_client.get_pool_by_address.return_value = {"pool_address": POOL_V3, "version": "v3", "fee_tier": 500}
        with patch("src.tools.pools.get_client", return_value=mock_client):
            from src.tools.pools import get_pool_by_address
            result = asyncio.run(get_pool_by_address(pool_address=POOL_V3))

        assert result["pool_address"] == POOL_V3
        mock_client.get_pool_by_address.assert_called_once_with(pool_address=POOL_V3, chain_id=1)


# get_swap_quote

class TestGetSwapQuoteTool:
    def test_returns_quote(self):
        mock_client = _make_client_mock()
        mock_client.get_swap_quote.return_value = {
            "token_in": {"symbol": "USDC"}, "token_out": {"symbol": "WETH"},
            "amount_in": 100.0, "amount_out": 0.033, "price": 0.00033,
            "fee_tier": 3000, "chain_id": 1,
        }
        with patch("src.tools.swaps.get_client", return_value=mock_client):
            from src.tools.swaps import get_swap_quote
            result = asyncio.run(get_swap_quote(token_in=USDC, token_out=WETH, amount_in="100", fee=3000))

        assert result["amount_in"] == 100.0
        mock_client.get_swap_quote.assert_called_once_with(
            token_in=USDC, token_out=WETH, amount_in="100", fee=3000, chain_id=1
        )

    def test_default_fee_is_3000(self):
        mock_client = _make_client_mock()
        mock_client.get_swap_quote.return_value = {}
        with patch("src.tools.swaps.get_client", return_value=mock_client):
            from src.tools.swaps import get_swap_quote
            asyncio.run(get_swap_quote(token_in=USDC, token_out=WETH, amount_in="1"))
        assert mock_client.get_swap_quote.call_args[1]["fee"] == 3000

    def test_passes_chain_id_from_client(self):
        mock_client = _make_client_mock(chain_id=42161)
        mock_client.get_swap_quote.return_value = {}
        with patch("src.tools.swaps.get_client", return_value=mock_client):
            from src.tools.swaps import get_swap_quote
            asyncio.run(get_swap_quote(token_in=USDC, token_out=WETH, amount_in="1"))
        assert mock_client.get_swap_quote.call_args[1]["chain_id"] == 42161


# execute_swap

class TestExecuteSwapTool:
    def test_calls_client_execute_swap(self):
        mock_client = _make_client_mock()
        mock_client.execute_swap.return_value = {
            "status": "success", "tx_hash": "0xabc",
            "token_in": {"symbol": "USDC", "amount": 1.0},
            "token_out": {"symbol": "WETH", "expected_amount": 0.000333},
            "slippage_bps": 50, "gas_used": 120000, "block_number": 20000000,
            "approval": "already_approved",
        }
        with patch("src.tools.swaps.get_client", return_value=mock_client):
            from src.tools.swaps import execute_swap
            result = asyncio.run(execute_swap(
                token_in=USDC, token_out=WETH, amount_in="1",
                slippage_bps=50, fee=3000, deadline_minutes=20,
            ))

        assert result["status"] == "success"
        mock_client.execute_swap.assert_called_once_with(
            token_in=USDC, token_out=WETH, amount_in="1",
            slippage_bps=50, fee=3000, deadline_minutes=20, chain_id=1,
        )

    def test_returns_error_when_no_private_key(self):
        mock_client = _make_client_mock()
        mock_client.execute_swap.return_value = {
            "error": "PRIVATE_KEY is not set — required for executing swaps"
        }
        with patch("src.tools.swaps.get_client", return_value=mock_client):
            from src.tools.swaps import execute_swap
            assert "error" in asyncio.run(execute_swap(token_in=USDC, token_out=WETH, amount_in="1"))

    def test_default_parameters(self):
        """execute_swap uses correct defaults when optional args are omitted."""
        mock_client = _make_client_mock()
        mock_client.execute_swap.return_value = {}
        with patch("src.tools.swaps.get_client", return_value=mock_client):
            from src.tools.swaps import execute_swap
            asyncio.run(execute_swap(token_in=USDC, token_out=WETH, amount_in="1"))

        kwargs = mock_client.execute_swap.call_args[1]
        assert kwargs["slippage_bps"]     == 50
        assert kwargs["fee"]              == 3000
        assert kwargs["deadline_minutes"] == 20


# get_token_info

class TestGetTokenInfoTool:
    def test_returns_token_info(self):
        mock_client = _make_client_mock()
        mock_client.erc20.name.return_value         = "Wrapped Ether"
        mock_client.erc20.symbol.return_value       = "WETH"
        mock_client.erc20.decimal.return_value      = 18
        mock_client.erc20.total_supply.return_value = 3_000_000 * 10**18

        with patch("src.tools.tokens.get_client", return_value=mock_client):
            from src.tools.tokens import get_token_info
            result = asyncio.run(get_token_info(token_address=WETH))

        assert result["address"]      == WETH
        assert result["name"]         == "Wrapped Ether"
        assert result["symbol"]       == "WETH"
        assert result["decimals"]     == 18
        assert result["total_supply"] == str(3_000_000 * 10**18)

    def test_total_supply_is_string(self):
        mock_client = _make_client_mock()
        mock_client.erc20.name.return_value         = "USD Coin"
        mock_client.erc20.symbol.return_value       = "USDC"
        mock_client.erc20.decimal.return_value      = 6
        mock_client.erc20.total_supply.return_value = 10**12

        with patch("src.tools.tokens.get_client", return_value=mock_client):
            from src.tools.tokens import get_token_info
            result = asyncio.run(get_token_info(token_address=USDC))

        assert isinstance(result["total_supply"], str)

    def test_all_fields_present(self):
        mock_client = _make_client_mock()
        mock_client.erc20.name.return_value         = "Tether USD"
        mock_client.erc20.symbol.return_value       = "USDT"
        mock_client.erc20.decimal.return_value      = 6
        mock_client.erc20.total_supply.return_value = 50_000_000_000 * 10**6

        with patch("src.tools.tokens.get_client", return_value=mock_client):
            from src.tools.tokens import get_token_info
            result = asyncio.run(get_token_info(token_address=USDT))

        for field in ("address", "name", "symbol", "decimals", "total_supply"):
            assert field in result, f"Missing field '{field}' in token info"
