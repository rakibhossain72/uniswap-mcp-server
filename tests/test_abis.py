"""
Tests for src/uniswap_client/abis/ — ABI loading and the ABI_MAP registry.
"""

import pytest
from src.uniswap_client.abis.get_abi import (
    _load_abi,
    get_erc20_abi,
    get_v2_factory_abi,
    get_v2_pair_abi,
    get_v3_factory_abi,
    get_v3_pool_abi,
    get_v3_quoter_abi,
    get_v3_router_abi,
    ABI_MAP,
)
from src.uniswap_client.abis import (
    ERC20_ABI,
    V2_FACTORY_ABI,
    V2_PAIR_ABI,
    V3_FACTORY_ABI,
    V3_POOL_ABI,
    V3_QUOTER_ABI,
    V3_ROUTER_ABI,
)


# Helpers

def _has_function(abi: list, name: str) -> bool:
    """Return True if the ABI contains an entry with the given name."""
    return any(
        entry.get("name") == name
        for entry in abi
        if isinstance(entry, dict)
    )


# _load_abi

class TestLoadAbi:
    def test_load_existing_file_returns_list(self):
        abi = _load_abi("ERC20_ABI.json")
        assert isinstance(abi, list)
        assert len(abi) > 0

    def test_load_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            _load_abi("NONEXISTENT_ABI.json")


# Individual getter functions

class TestAbiGetters:
    @pytest.mark.parametrize("getter,expected_fn", [
        (get_erc20_abi,      "transfer"),
        (get_v2_factory_abi, "getPair"),
        (get_v2_pair_abi,    "getReserves"),
        (get_v3_factory_abi, "getPool"),
        (get_v3_pool_abi,    "slot0"),
        (get_v3_quoter_abi,  "quoteExactInputSingle"),
        (get_v3_router_abi,  "exactInputSingle"),
    ])
    def test_getter_returns_list_with_expected_function(self, getter, expected_fn):
        abi = getter()
        assert isinstance(abi, list)
        assert _has_function(abi, expected_fn), (
            f"{getter.__name__}() should contain '{expected_fn}'"
        )

    def test_erc20_has_standard_functions(self):
        abi = get_erc20_abi()
        for fn_name in ("transfer", "approve", "allowance", "balanceOf", "decimals", "symbol"):
            assert _has_function(abi, fn_name), f"ERC20 ABI missing '{fn_name}'"

    def test_v2_factory_has_get_pair(self):
        assert _has_function(get_v2_factory_abi(), "getPair")

    def test_v2_pair_has_get_reserves(self):
        assert _has_function(get_v2_pair_abi(), "getReserves")

    def test_v3_factory_has_get_pool(self):
        assert _has_function(get_v3_factory_abi(), "getPool")

    def test_v3_pool_has_slot0(self):
        assert _has_function(get_v3_pool_abi(), "slot0")

    def test_v3_quoter_has_quote_exact_input_single(self):
        assert _has_function(get_v3_quoter_abi(), "quoteExactInputSingle")

    def test_v3_router_has_exact_input_single(self):
        assert _has_function(get_v3_router_abi(), "exactInputSingle")

    def test_each_getter_returns_new_list_each_call(self):
        """ABI loaders should not share mutable state between calls."""
        a = get_erc20_abi()
        b = get_erc20_abi()
        assert a == b
        assert a is not b  # fresh load each time


# ABI_MAP registry

class TestAbiMap:
    def test_all_keys_present(self):
        expected_keys = {
            "ERC20", "V2_FACTORY", "V2_PAIR",
            "V3_FACTORY", "V3_POOL", "V3_QUOTER", "V3_ROUTER",
        }
        assert expected_keys == set(ABI_MAP.keys())

    def test_all_values_are_callable(self):
        for key, fn in ABI_MAP.items():
            assert callable(fn), f"ABI_MAP['{key}'] is not callable"

    def test_calling_map_entries_returns_lists(self):
        for key, fn in ABI_MAP.items():
            result = fn()
            assert isinstance(result, list), f"ABI_MAP['{key}']() did not return a list"
            assert len(result) > 0, f"ABI_MAP['{key}']() returned an empty list"


# Lazy-loader wrappers from abis/__init__.py

class TestLazyAbiWrappers:
    @pytest.mark.parametrize("wrapper,expected_fn", [
        (ERC20_ABI,      "transfer"),
        (V2_FACTORY_ABI, "getPair"),
        (V2_PAIR_ABI,    "getReserves"),
        (V3_FACTORY_ABI, "getPool"),
        (V3_POOL_ABI,    "slot0"),
        (V3_QUOTER_ABI,  "quoteExactInputSingle"),
        (V3_ROUTER_ABI,  "exactInputSingle"),
    ])
    def test_wrapper_returns_list_with_expected_function(self, wrapper, expected_fn):
        abi = wrapper()
        assert isinstance(abi, list)
        assert _has_function(abi, expected_fn)

    def test_wrappers_are_callable(self):
        for wrapper in (
            ERC20_ABI, V2_FACTORY_ABI, V2_PAIR_ABI,
            V3_FACTORY_ABI, V3_POOL_ABI, V3_QUOTER_ABI, V3_ROUTER_ABI,
        ):
            assert callable(wrapper)
