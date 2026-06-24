"""
Tests for contract wrappers:
  - BaseContract
  - ERC20
  - V2Factory / V2Pair
  - V3Factory / V3Pool / V3Quoter / V3Router
All Web3 / on-chain calls are mocked — no network required.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from web3 import Web3

from tests.conftest import WETH, USDC, USDT, POOL_V3, PAIR_V2, ZERO_ADDR


# Helpers

def _make_contract_mock():
    """Return a mock for web3.eth.contract(...)."""
    return MagicMock()


def _mock_web3_for_contract(chain_id=1):
    """Return a MagicMock Web3 that won't trigger real network calls."""
    w3 = MagicMock(spec=Web3)
    w3.eth = MagicMock()
    w3.eth.chain_id = chain_id
    w3.to_checksum_address = Web3.to_checksum_address
    return w3


# BaseContract

class TestBaseContract:
    def test_stores_web3_address_and_abi(self):
        from src.uniswap_client.contracts.base import BaseContract
        w3 = _mock_web3_for_contract()
        w3.eth.contract.return_value = MagicMock()

        bc = BaseContract(w3, WETH, [{"type": "function", "name": "foo"}])

        assert bc.web3 is w3
        assert bc.address == Web3.to_checksum_address(WETH)

    def test_checksum_converts_lowercase(self):
        from src.uniswap_client.contracts.base import BaseContract
        w3 = _mock_web3_for_contract()
        w3.eth.contract.return_value = MagicMock()

        bc = BaseContract(w3, WETH.lower(), [])
        assert bc.address == Web3.to_checksum_address(WETH)

    def test_checksum_helper(self):
        from src.uniswap_client.contracts.base import BaseContract
        w3 = _mock_web3_for_contract()
        w3.eth.contract.return_value = MagicMock()

        bc = BaseContract(w3, WETH, [])
        assert bc._checksum(USDC.lower()) == Web3.to_checksum_address(USDC)

    def test_contract_attribute_initialised(self):
        from src.uniswap_client.contracts.base import BaseContract
        w3 = _mock_web3_for_contract()
        contract_mock = MagicMock()
        w3.eth.contract.return_value = contract_mock

        bc = BaseContract(w3, WETH, [])
        assert bc.contract is contract_mock


# ERC20

class TestERC20:
    """ERC20 wrapper delegates every call to the underlying contract."""

    def _make_erc20(self):
        from src.uniswap_client.contracts.erc20 import ERC20
        w3 = MagicMock()
        w3.to_checksum_address = Web3.to_checksum_address
        self._contract = MagicMock()
        w3.eth.contract.return_value = self._contract
        return ERC20(w3)

    def test_decimal_calls_contract(self):
        erc20 = self._make_erc20()
        self._contract.functions.decimals.return_value.call.return_value = 18
        assert erc20.decimal(USDC) == 18

    def test_symbol_calls_contract(self):
        erc20 = self._make_erc20()
        self._contract.functions.symbol.return_value.call.return_value = "USDC"
        assert erc20.symbol(USDC) == "USDC"

    def test_name_calls_contract(self):
        erc20 = self._make_erc20()
        self._contract.functions.name.return_value.call.return_value = "USD Coin"
        assert erc20.name(USDC) == "USD Coin"

    def test_total_supply_calls_contract(self):
        erc20 = self._make_erc20()
        self._contract.functions.totalSupply.return_value.call.return_value = 10**18
        assert erc20.total_supply(USDC) == 10**18

    def test_balance_of_calls_contract(self):
        erc20 = self._make_erc20()
        self._contract.functions.balanceOf.return_value.call.return_value = 500_000
        assert erc20.balance_of(USDC, WETH) == 500_000

    def test_allowance_calls_contract(self):
        erc20 = self._make_erc20()
        self._contract.functions.allowance.return_value.call.return_value = 2**256 - 1
        assert erc20.allowance(USDC, WETH, USDT) == 2**256 - 1

    def test_approve_returns_contract_function(self):
        erc20 = self._make_erc20()
        approve_fn = MagicMock()
        self._contract.functions.approve.return_value = approve_fn
        assert erc20.approve(USDC, WETH, 1000) is approve_fn

    def test_is_contract_true_when_code_present(self):
        erc20 = self._make_erc20()
        erc20.web3.eth.get_code.return_value = b"\x60\x60"
        assert erc20.is_contract(USDC) is True

    def test_is_contract_false_for_eoa(self):
        erc20 = self._make_erc20()
        erc20.web3.eth.get_code.return_value = b""
        assert erc20.is_contract(USDC) is False

    def test_format_amount_uses_decimals(self):
        erc20 = self._make_erc20()
        self._contract.functions.decimals.return_value.call.return_value = 6
        assert erc20.format_amount(USDC, 1_000_000) == pytest.approx(1.0)

    def test_format_amount_18_decimals(self):
        erc20 = self._make_erc20()
        self._contract.functions.decimals.return_value.call.return_value = 18
        assert erc20.format_amount(WETH, 1 * 10**18) == pytest.approx(1.0)

    def test_parse_amount_uses_decimals(self):
        erc20 = self._make_erc20()
        self._contract.functions.decimals.return_value.call.return_value = 6
        assert erc20.parse_amount(USDC, 1.5) == 1_500_000

    def test_parse_amount_18_decimals(self):
        erc20 = self._make_erc20()
        self._contract.functions.decimals.return_value.call.return_value = 18
        assert erc20.parse_amount(WETH, 2.0) == 2 * 10**18

    def test_get_contract_uses_checksum_address(self):
        erc20 = self._make_erc20()
        self._contract.functions.decimals.return_value.call.return_value = 18
        erc20.decimal(USDC.lower())
        called_address = erc20.web3.eth.contract.call_args[1]["address"]
        assert called_address == Web3.to_checksum_address(USDC)


# V2Factory

class TestV2Factory:
    def _make_factory(self):
        from src.uniswap_client.contracts.v2_factory import V2Factory
        w3 = MagicMock()
        w3.to_checksum_address = Web3.to_checksum_address
        self._contract = MagicMock()
        w3.eth.contract.return_value = self._contract
        return V2Factory(w3, "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")

    def test_get_pair_returns_address(self):
        factory = self._make_factory()
        self._contract.functions.getPair.return_value.call.return_value = PAIR_V2
        assert factory.get_pair(USDC, WETH) == PAIR_V2

    def test_get_pair_zero_when_not_found(self):
        factory = self._make_factory()
        self._contract.functions.getPair.return_value.call.return_value = ZERO_ADDR
        assert factory.get_pair(USDC, USDT) == ZERO_ADDR

    def test_all_pairs_length(self):
        factory = self._make_factory()
        self._contract.functions.allPairsLength.return_value.call.return_value = 1000
        assert factory.all_pairs_length() == 1000

    def test_all_pairs_by_index(self):
        factory = self._make_factory()
        self._contract.functions.allPairs.return_value.call.return_value = PAIR_V2
        assert factory.all_pairs(0) == PAIR_V2


# V2Pair

class TestV2Pair:
    def _make_pair(self):
        from src.uniswap_client.contracts.v2_pair import V2Pair
        w3 = MagicMock()
        w3.to_checksum_address = Web3.to_checksum_address
        self._contract = MagicMock()
        w3.eth.contract.return_value = self._contract
        return V2Pair(w3, PAIR_V2)

    def test_get_reserves(self):
        pair = self._make_pair()
        reserves = (1_000_000 * 10**6, 500 * 10**18, 1700000000)
        self._contract.functions.getReserves.return_value.call.return_value = reserves
        assert pair.get_reserves() == reserves

    def test_token0(self):
        pair = self._make_pair()
        self._contract.functions.token0.return_value.call.return_value = USDC
        assert pair.token0() == USDC

    def test_token1(self):
        pair = self._make_pair()
        self._contract.functions.token1.return_value.call.return_value = WETH
        assert pair.token1() == WETH

    def test_total_supply(self):
        pair = self._make_pair()
        self._contract.functions.totalSupply.return_value.call.return_value = 10**18
        assert pair.total_supply() == 10**18

    def test_balance_of(self):
        pair = self._make_pair()
        self._contract.functions.balanceOf.return_value.call.return_value = 5000
        assert pair.balance_of(WETH) == 5000


# V3Factory

class TestV3Factory:
    def _make_factory(self):
        from src.uniswap_client.contracts.v3_factory import V3Factory
        w3 = MagicMock()
        w3.to_checksum_address = Web3.to_checksum_address
        self._contract = MagicMock()
        w3.eth.contract.return_value = self._contract
        return V3Factory(w3, "0x1F98431c8aD98523631AE4a59f267346ea31F984")

    def test_get_pool_returns_address(self):
        factory = self._make_factory()
        self._contract.functions.getPool.return_value.call.return_value = POOL_V3
        assert factory.get_pool(USDC, WETH, 500) == POOL_V3

    def test_get_pool_zero_when_not_found(self):
        factory = self._make_factory()
        self._contract.functions.getPool.return_value.call.return_value = ZERO_ADDR
        assert factory.get_pool(USDC, USDT, 100) == ZERO_ADDR

    def test_fee_amount_tick_spacing(self):
        factory = self._make_factory()
        self._contract.functions.feeAmountTickSpacing.return_value.call.return_value = 10
        assert factory.fee_amount_tick_spacing(500) == 10

    def test_owner(self):
        factory = self._make_factory()
        self._contract.functions.owner.return_value.call.return_value = WETH
        assert factory.owner() == WETH


# V3Pool

class TestV3Pool:
    def _make_pool(self):
        from src.uniswap_client.contracts.v3_pool import V3Pool
        w3 = MagicMock()
        w3.to_checksum_address = Web3.to_checksum_address
        self._contract = MagicMock()
        w3.eth.contract.return_value = self._contract
        return V3Pool(w3, POOL_V3)

    def test_slot0(self):
        pool = self._make_pool()
        slot0_data = (2**96, 202919, 0, 1, 1, 0, True)
        self._contract.functions.slot0.return_value.call.return_value = slot0_data
        assert pool.slot0() == slot0_data

    def test_liquidity(self):
        pool = self._make_pool()
        self._contract.functions.liquidity.return_value.call.return_value = 123456789
        assert pool.liquidity() == 123456789

    def test_fee(self):
        pool = self._make_pool()
        self._contract.functions.fee.return_value.call.return_value = 500
        assert pool.fee() == 500

    def test_token0(self):
        pool = self._make_pool()
        self._contract.functions.token0.return_value.call.return_value = USDC
        assert pool.token0() == USDC

    def test_token1(self):
        pool = self._make_pool()
        self._contract.functions.token1.return_value.call.return_value = WETH
        assert pool.token1() == WETH

    def test_tick_spacing(self):
        pool = self._make_pool()
        self._contract.functions.tickSpacing.return_value.call.return_value = 10
        assert pool.tick_spacing() == 10

    def test_fee_growth_global0(self):
        pool = self._make_pool()
        self._contract.functions.feeGrowthGlobal0X128.return_value.call.return_value = 99
        assert pool.fee_growth_global0_x128() == 99


# V3Quoter

class TestV3Quoter:
    def _make_quoter(self):
        from src.uniswap_client.contracts.v3_quoter import V3Quoter
        w3 = MagicMock()
        w3.to_checksum_address = Web3.to_checksum_address
        self._contract = MagicMock()
        w3.eth.contract.return_value = self._contract
        return V3Quoter(w3, "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6")

    def test_quote_exact_input_single(self):
        quoter = self._make_quoter()
        self._contract.functions.quoteExactInputSingle.return_value.call.return_value = 3000 * 10**6
        assert quoter.quote_exact_input_single(USDC, WETH, 3000, 10**6, 0) == 3000 * 10**6

    def test_quote_exact_output_single(self):
        quoter = self._make_quoter()
        self._contract.functions.quoteExactOutputSingle.return_value.call.return_value = 10**6
        assert quoter.quote_exact_output_single(USDC, WETH, 3000, 3000 * 10**6, 0) == 10**6

    def test_quote_exact_input_single_checksums_addresses(self):
        """Addresses are checksummed before being passed to the contract."""
        quoter = self._make_quoter()
        self._contract.functions.quoteExactInputSingle.return_value.call.return_value = 1
        quoter.quote_exact_input_single(USDC.lower(), WETH.lower(), 500, 1000, 0)
        args = self._contract.functions.quoteExactInputSingle.call_args[0]
        assert args[0] == Web3.to_checksum_address(USDC)
        assert args[1] == Web3.to_checksum_address(WETH)


# V3Router

class TestV3Router:
    def _make_router(self):
        from src.uniswap_client.contracts.v3_router import V3Router
        w3 = MagicMock()
        w3.to_checksum_address = Web3.to_checksum_address
        self._contract = MagicMock()
        w3.eth.contract.return_value = self._contract
        return V3Router(w3, "0xE592427A0AEce92De3Edee1F18E0157C05861564")

    def test_exact_input_single_returns_contract_fn(self):
        router = self._make_router()
        fn_mock = MagicMock()
        self._contract.functions.exactInputSingle.return_value = fn_mock
        params = {"tokenIn": USDC, "tokenOut": WETH, "fee": 3000,
                  "recipient": WETH, "deadline": 9999999,
                  "amountIn": 10**6, "amountOutMinimum": 0, "sqrtPriceLimitX96": 0}
        assert router.exact_input_single(params) is fn_mock

    def test_multicall_returns_contract_fn(self):
        router = self._make_router()
        fn_mock = MagicMock()
        self._contract.functions.multicall.return_value = fn_mock
        assert router.multicall([b"data"]) is fn_mock

    def test_unwrap_weth_checksums_recipient(self):
        router = self._make_router()
        self._contract.functions.unwrapWETH9.return_value = MagicMock()
        router.unwrap_weth(0, WETH.lower())
        args = self._contract.functions.unwrapWETH9.call_args[0]
        assert args[1] == Web3.to_checksum_address(WETH)
