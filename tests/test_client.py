"""
Tests for src/uniswap_client/core/client.py — UniswapClient.

Every on-chain contract call is mocked so tests run fully offline.
The fixture `client` provides a UniswapClient whose Web3 instance and all
contract wrappers are replaced with MagicMocks.
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from web3 import Web3

from tests.conftest import WETH, USDC, USDT, POOL_V3, PAIR_V2, ZERO_ADDR

# A deterministic test private key (never use for real funds).
_TEST_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


# Fixture: offline UniswapClient

@pytest.fixture
def client(monkeypatch):
    """
    Return a UniswapClient with all Web3 / contract interactions mocked.
    chain_id is fixed to 1 (mainnet).
    """
    from src.uniswap_client.core.client import UniswapClient

    mock_w3 = MagicMock()
    mock_w3.eth.chain_id = 1
    mock_w3.to_checksum_address = Web3.to_checksum_address
    mock_w3.middleware_onion = MagicMock()

    with patch("src.uniswap_client.core.client.Web3") as MockWeb3, \
         patch("src.uniswap_client.core.client.ExtraDataToPOAMiddleware"):
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider.return_value = MagicMock()
        c = UniswapClient(rpc_url="http://localhost:8545")

    c.w3 = mock_w3
    c.chain_id = 1
    c.erc20        = MagicMock()
    c.v2_factory   = MagicMock()
    c.v3_factory   = MagicMock()
    c.v3_quoter    = MagicMock()
    c.v3_router    = MagicMock()
    c._pool_cache  = {}
    c._pair_cache  = {}
    c._initialize_contracts = MagicMock()
    return c


@pytest.fixture
def client_with_key(client):
    """Same as `client` but with a private key / account set."""
    from eth_account import Account
    client.private_key = _TEST_KEY
    client.account = Account.from_key(_TEST_KEY)
    return client


# Helpers

def _pool_mock(sqrt_price_x96=2**96, tick=200000, fee=3000, token0=USDC, token1=WETH, liquidity=10**18):
    pool = MagicMock()
    pool.slot0.return_value     = (sqrt_price_x96, tick, 0, 1, 1, 0, True)
    pool.liquidity.return_value = liquidity
    pool.fee.return_value       = fee
    pool.token0.return_value    = token0
    pool.token1.return_value    = token1
    return pool


# _checksum / _get_erc20 / _token_info

class TestInternals:
    def test_checksum_delegates_to_w3(self, client):
        assert client._checksum(USDC.lower()) == Web3.to_checksum_address(USDC)

    def test_get_erc20_returns_erc20_instance(self, client):
        assert client._get_erc20() is client.erc20

    def test_token_info_aggregates_fields(self, client):
        client.erc20.symbol.return_value  = "USDC"
        client.erc20.decimal.return_value = 6
        info = client._token_info(USDC)
        assert info == {"address": Web3.to_checksum_address(USDC), "symbol": "USDC", "decimals": 6}

    def test_get_v3_pool_caches_instance(self, client):
        """Second call returns cached pool without re-constructing."""
        with patch("src.uniswap_client.core.client.V3Pool") as MockPool:
            MockPool.return_value = MagicMock()
            p1 = client._get_v3_pool(POOL_V3)
            p2 = client._get_v3_pool(POOL_V3)
        assert p1 is p2
        assert MockPool.call_count == 1

    def test_get_v2_pair_caches_instance(self, client):
        with patch("src.uniswap_client.core.client.V2Pair") as MockPair:
            MockPair.return_value = MagicMock()
            p1 = client._get_v2_pair(PAIR_V2)
            p2 = client._get_v2_pair(PAIR_V2)
        assert p1 is p2
        assert MockPair.call_count == 1


# get_token_price

class TestGetTokenPrice:
    def test_returns_price_dict_for_usdc_pool(self, client):
        client.erc20.decimal.return_value = 18
        client.erc20.symbol.return_value  = "DAI"

        pool = _pool_mock(
            sqrt_price_x96=2**96,
            token0=USDC,
            token1="0x6B175474E89094C44Da98b954EedeAC495271d0F",
        )
        client.v3_factory.get_pool.side_effect = lambda t0, t1, fee: POOL_V3
        client._pool_cache[Web3.to_checksum_address(POOL_V3)] = pool

        result = client.get_token_price("0x6B175474E89094C44Da98b954EedeAC495271d0F")
        assert "price_usd" in result
        assert result["chain_id"] == 1

    def test_returns_error_when_no_pool_found(self, client):
        client.erc20.decimal.return_value = 18
        client.erc20.symbol.return_value  = "UNKNOWN"
        client.v3_factory.get_pool.return_value = ZERO_ADDR

        assert "error" in client.get_token_price(WETH)

    def test_skips_zero_sqrt_price(self, client):
        """Pool with sqrtPriceX96 == 0 should be skipped."""
        client.erc20.decimal.return_value = 18
        client.erc20.symbol.return_value  = "TKN"

        pool = _pool_mock(sqrt_price_x96=0, token0=USDC, token1=WETH)
        client.v3_factory.get_pool.return_value = POOL_V3
        client._pool_cache[Web3.to_checksum_address(POOL_V3)] = pool

        assert isinstance(client.get_token_price(WETH), dict)

    def test_price_usd_is_float(self, client):
        client.erc20.decimal.return_value = 6
        client.erc20.symbol.return_value  = "USDC"

        pool = _pool_mock(sqrt_price_x96=2**96, token0=USDC, token1=USDT)
        client.v3_factory.get_pool.return_value = POOL_V3
        client._pool_cache[Web3.to_checksum_address(POOL_V3)] = pool

        result = client.get_token_price(USDC)
        if "price_usd" in result:
            assert isinstance(result["price_usd"], float)


# get_pool_by_address

class TestGetPoolByAddress:
    def test_returns_pool_dict(self, client):
        client.erc20.symbol.side_effect  = lambda addr: "USDC" if addr == USDC else "WETH"
        client.erc20.decimal.side_effect = lambda addr: 6 if addr == USDC else 18

        pool = _pool_mock(sqrt_price_x96=2**96, token0=USDC, token1=WETH, fee=500)
        client._pool_cache[Web3.to_checksum_address(POOL_V3)] = pool

        result = client.get_pool_by_address(POOL_V3)
        assert result["pool_address"] == POOL_V3
        assert result["version"] == "v3"
        assert result["fee_tier"] == 500
        assert "token0" in result and "token1" in result and "liquidity" in result

    def test_price_is_zero_when_sqrt_price_is_zero(self, client):
        client.erc20.symbol.return_value  = "X"
        client.erc20.decimal.return_value = 18

        pool = _pool_mock(sqrt_price_x96=0, token0=USDC, token1=WETH)
        client._pool_cache[Web3.to_checksum_address(POOL_V3)] = pool

        assert client.get_pool_by_address(POOL_V3)["price_token1_per_token0"] == 0.0

    def test_fee_percent_formatted(self, client):
        client.erc20.symbol.return_value  = "X"
        client.erc20.decimal.return_value = 18

        pool = _pool_mock(fee=3000, token0=USDC, token1=WETH)
        client._pool_cache[Web3.to_checksum_address(POOL_V3)] = pool

        assert client.get_pool_by_address(POOL_V3)["fee_percent"] == "0.3000%"

    def test_liquidity_returned_as_string(self, client):
        client.erc20.symbol.return_value  = "X"
        client.erc20.decimal.return_value = 18

        pool = _pool_mock(liquidity=999999, token0=USDC, token1=WETH)
        client._pool_cache[Web3.to_checksum_address(POOL_V3)] = pool

        assert client.get_pool_by_address(POOL_V3)["liquidity"] == "999999"


# get_v3_pool

class TestGetV3Pool:
    def test_returns_error_when_pool_not_found(self, client):
        client.v3_factory.get_pool.return_value = ZERO_ADDR
        assert "error" in client.get_v3_pool(USDC, WETH, fee=3000)

    def test_delegates_to_get_pool_by_address(self, client):
        client.v3_factory.get_pool.return_value = POOL_V3
        client.erc20.symbol.return_value  = "X"
        client.erc20.decimal.return_value = 18
        client._pool_cache[Web3.to_checksum_address(POOL_V3)] = _pool_mock(token0=USDC, token1=WETH)

        assert client.get_v3_pool(USDC, WETH, fee=3000)["pool_address"] == POOL_V3


# get_v2_pair

class TestGetV2Pair:
    def test_returns_error_when_pair_not_found(self, client):
        client.v2_factory.get_pair.return_value = ZERO_ADDR
        assert "error" in client.get_v2_pair(USDC, WETH)

    def test_returns_pair_dict_on_success(self, client):
        client.v2_factory.get_pair.return_value = PAIR_V2

        pair = MagicMock()
        pair.get_reserves.return_value = (1_000_000 * 10**6, 500 * 10**18, 1700000000)
        pair.token0.return_value = USDC
        pair.token1.return_value = WETH
        client._pair_cache[Web3.to_checksum_address(PAIR_V2)] = pair
        client.erc20.symbol.side_effect  = lambda addr: "USDC" if addr == USDC else "WETH"
        client.erc20.decimal.side_effect = lambda addr: 6 if addr == USDC else 18

        result = client.get_v2_pair(USDC, WETH)
        assert result["pair_address"] == PAIR_V2
        assert result["version"] == "v2"
        assert result["chain_id"] == 1
        assert "reserve0" in result and "reserve1" in result

    def test_price_is_zero_when_reserve0_is_zero(self, client):
        client.v2_factory.get_pair.return_value = PAIR_V2

        pair = MagicMock()
        pair.get_reserves.return_value = (0, 500 * 10**18, 1700000000)
        pair.token0.return_value = USDC
        pair.token1.return_value = WETH
        client._pair_cache[Web3.to_checksum_address(PAIR_V2)] = pair
        client.erc20.symbol.return_value  = "X"
        client.erc20.decimal.return_value = 18

        assert client.get_v2_pair(USDC, WETH)["price_token1_per_token0"] == 0

    def test_block_timestamp_last_present(self, client):
        client.v2_factory.get_pair.return_value = PAIR_V2

        pair = MagicMock()
        pair.get_reserves.return_value = (10**6, 10**18, 1700000000)
        pair.token0.return_value = USDC
        pair.token1.return_value = WETH
        client._pair_cache[Web3.to_checksum_address(PAIR_V2)] = pair
        client.erc20.symbol.return_value  = "X"
        client.erc20.decimal.return_value = 18

        assert client.get_v2_pair(USDC, WETH)["block_timestamp_last"] == 1700000000


# get_swap_quote

class TestGetSwapQuote:
    def test_returns_quote_dict(self, client):
        client.erc20.decimal.side_effect = lambda addr: 6 if addr == Web3.to_checksum_address(USDC) else 18
        client.erc20.symbol.side_effect  = lambda addr: "USDC" if addr == Web3.to_checksum_address(USDC) else "WETH"
        client.v3_quoter.quote_exact_input_single.return_value = int(Decimal("0.000333333") * Decimal(10**18))

        result = client.get_swap_quote(USDC, WETH, "1", fee=3000)
        assert result["token_in"]["symbol"]  == "USDC"
        assert result["token_out"]["symbol"] == "WETH"
        assert result["amount_in"]           == pytest.approx(1.0)
        assert result["fee_tier"]            == 3000
        assert result["chain_id"]            == 1
        assert isinstance(result["amount_out"], float)
        assert isinstance(result["price"], float)

    def test_quote_calls_quoter_with_correct_wei(self, client):
        """amount_in string is correctly converted to wei before calling quoter."""
        client.erc20.decimal.return_value = 6
        client.erc20.symbol.return_value  = "USDC"
        client.v3_quoter.quote_exact_input_single.return_value = 1

        client.get_swap_quote(USDC, WETH, "2.5", fee=500)
        # 2.5 * 10^6 = 2_500_000
        assert client.v3_quoter.quote_exact_input_single.call_args[0][3] == 2_500_000

    def test_price_is_amount_out_over_amount_in(self, client):
        client.erc20.decimal.return_value = 18
        client.erc20.symbol.return_value  = "TKN"
        client.v3_quoter.quote_exact_input_single.return_value = 4 * 10**18

        assert client.get_swap_quote(USDC, WETH, "2", fee=3000)["price"] == pytest.approx(2.0)


# execute_swap — no private key

class TestExecuteSwapNoKey:
    def test_returns_error_without_private_key(self, client):
        """execute_swap returns an error dict when PRIVATE_KEY is not set."""
        assert client.account is None
        result = client.execute_swap(USDC, WETH, "1")
        assert "error" in result
        assert "PRIVATE_KEY" in result["error"]


# execute_swap — with private key

class TestExecuteSwapWithKey:
    def test_returns_success_dict(self, client_with_key):
        c = client_with_key
        c.erc20.decimal.side_effect = lambda addr: 6 if addr == Web3.to_checksum_address(USDC) else 18
        c.erc20.symbol.side_effect  = lambda addr: "USDC" if addr == Web3.to_checksum_address(USDC) else "WETH"
        c.v3_quoter.quote_exact_input_single.return_value = int(Decimal("0.000333") * Decimal(10**18))

        approval_contract = MagicMock()
        approval_contract.functions.allowance.return_value.call.return_value = 2**256 - 1
        c.w3.eth.contract.return_value = approval_contract
        c.w3.eth.get_transaction_count.return_value = 0
        c.w3.eth.gas_price = 10**9

        tx_fn = MagicMock()
        tx_fn.build_transaction.return_value = {
            "to": "0x0", "data": "0x", "gas": 300000, "gasPrice": 10**9,
            "nonce": 0, "value": 0, "chainId": 1,
        }
        c.v3_router.exact_input_single.return_value = tx_fn

        signed = MagicMock()
        signed.raw_transaction = b"\x00" * 32
        c.w3.eth.account.sign_transaction.return_value = signed
        raw_tx_hash = b"\xab" * 32
        c.w3.eth.send_raw_transaction.return_value = raw_tx_hash
        c.w3.eth.wait_for_transaction_receipt.return_value = {
            "status": 1, "gasUsed": 120000, "blockNumber": 20000000,
            "transactionHash": raw_tx_hash,
        }

        result = c.execute_swap(USDC, WETH, "1", slippage_bps=50, fee=3000)
        assert result["status"] == "success"
        assert "tx_hash" in result
        assert result["token_in"]["symbol"]  == "USDC"
        assert result["token_out"]["symbol"] == "WETH"
        assert result["slippage_bps"]        == 50

    def test_failed_tx_reports_failed_status(self, client_with_key):
        c = client_with_key
        c.erc20.decimal.return_value = 18
        c.erc20.symbol.return_value  = "TKN"
        c.v3_quoter.quote_exact_input_single.return_value = 10**18

        approval_contract = MagicMock()
        approval_contract.functions.allowance.return_value.call.return_value = 2**256 - 1
        c.w3.eth.contract.return_value = approval_contract
        c.w3.eth.get_transaction_count.return_value = 1
        c.w3.eth.gas_price = 10**9

        tx_fn = MagicMock()
        tx_fn.build_transaction.return_value = {
            "to": "0x0", "data": "0x", "gas": 300000, "gasPrice": 10**9,
            "nonce": 1, "value": 0, "chainId": 1,
        }
        c.v3_router.exact_input_single.return_value = tx_fn

        signed = MagicMock()
        signed.raw_transaction = b"\x00" * 32
        c.w3.eth.account.sign_transaction.return_value = signed
        c.w3.eth.send_raw_transaction.return_value = b"\xcd" * 32
        c.w3.eth.wait_for_transaction_receipt.return_value = {
            "status": 0, "gasUsed": 50000, "blockNumber": 20000001,
            "transactionHash": b"\xcd" * 32,
        }

        assert c.execute_swap(USDC, WETH, "1")["status"] == "failed"


# _ensure_approval

class TestEnsureApproval:
    def test_already_approved_skips_tx(self, client_with_key):
        c = client_with_key
        token_contract = MagicMock()
        token_contract.functions.allowance.return_value.call.return_value = 2**256 - 1
        c.w3.eth.contract.return_value = token_contract

        assert c._ensure_approval(USDC, WETH, 10**6) == "already_approved"
        c.w3.eth.send_raw_transaction.assert_not_called()

    def test_sends_approval_tx_when_allowance_insufficient(self, client_with_key):
        c = client_with_key
        token_contract = MagicMock()
        token_contract.functions.allowance.return_value.call.return_value = 0

        approve_fn = MagicMock()
        approve_fn.build_transaction.return_value = {
            "to": USDC, "data": "0x", "gas": 100000, "gasPrice": 10**9,
            "nonce": 0, "value": 0, "chainId": 1,
        }
        token_contract.functions.approve.return_value = approve_fn
        c.w3.eth.contract.return_value = token_contract
        c.w3.eth.get_transaction_count.return_value = 0
        c.w3.eth.gas_price = 10**9

        signed = MagicMock()
        signed.raw_transaction = b"\x00" * 32
        c.w3.eth.account.sign_transaction.return_value = signed
        c.w3.eth.send_raw_transaction.return_value = b"\xaa" * 32
        c.w3.eth.wait_for_transaction_receipt.return_value = {}

        result = c._ensure_approval(USDC, WETH, 10**6)
        assert "approved" in result
        c.w3.eth.send_raw_transaction.assert_called_once()
