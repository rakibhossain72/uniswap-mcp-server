"""
Tests for src/uniswap_client/addresses.py —
ChainId enum, ProtocolAddresses dataclass, and get_addresses().
"""

import pytest
from src.uniswap_client.addresses import (
    ChainId,
    ProtocolAddresses,
    get_addresses,
    _CHAIN_ADDRESSES,
)


# ChainId enum

class TestChainId:
    def test_known_chain_ids_exist(self):
        assert ChainId.MAINNET == 1
        assert ChainId.POLYGON == 137
        assert ChainId.OPTIMISM == 10
        assert ChainId.ARBITRUM == 42161

    def test_chain_id_from_int(self):
        assert ChainId(1) is ChainId.MAINNET
        assert ChainId(137) is ChainId.POLYGON
        assert ChainId(10) is ChainId.OPTIMISM
        assert ChainId(42161) is ChainId.ARBITRUM

    def test_unknown_chain_id_raises(self):
        with pytest.raises(ValueError):
            ChainId(9999)

    def test_chain_id_is_int_enum(self):
        from enum import IntEnum
        assert isinstance(ChainId.MAINNET, int)
        assert issubclass(ChainId, IntEnum)

    def test_all_supported_chains_present(self):
        expected = {1, 137, 10, 42161}
        actual = {c.value for c in ChainId}
        assert actual == expected


# ProtocolAddresses dataclass

VALID_KWARGS = dict(
    v2_factory="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    v3_factory="0x1F98431c8aD98523631AE4a59f267346ea31F984",
    v3_quoter="0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
    v3_router="0xE592427A0AEce92De3Edee1F18E0157C05861564",
    weth="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    usdc="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    usdt="0xdAC17F958D2ee523a2206206994597C13D831ec7",
)


class TestProtocolAddresses:
    def test_valid_construction(self):
        addrs = ProtocolAddresses(**VALID_KWARGS)
        assert addrs.v2_factory == VALID_KWARGS["v2_factory"]
        assert addrs.weth == VALID_KWARGS["weth"]

    def test_is_frozen(self):
        """ProtocolAddresses is immutable after construction."""
        addrs = ProtocolAddresses(**VALID_KWARGS)
        with pytest.raises((AttributeError, TypeError)):
            addrs.weth = "0x0000000000000000000000000000000000000000"  # type: ignore[misc]

    def test_invalid_address_too_short(self):
        bad = dict(VALID_KWARGS)
        bad["weth"] = "0xshort"
        with pytest.raises(ValueError, match="weth"):
            ProtocolAddresses(**bad)

    def test_invalid_address_missing_0x_prefix(self):
        bad = dict(VALID_KWARGS)
        bad["usdc"] = "A0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # no 0x
        with pytest.raises(ValueError, match="usdc"):
            ProtocolAddresses(**bad)

    def test_invalid_address_not_a_string(self):
        bad = dict(VALID_KWARGS)
        bad["v3_router"] = 12345  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="v3_router"):
            ProtocolAddresses(**bad)

    def test_invalid_address_too_long(self):
        bad = dict(VALID_KWARGS)
        bad["usdt"] = "0x" + "a" * 41  # 43 chars total instead of 42
        with pytest.raises(ValueError, match="usdt"):
            ProtocolAddresses(**bad)

    def test_all_seven_fields_stored(self):
        addrs = ProtocolAddresses(**VALID_KWARGS)
        for field, value in VALID_KWARGS.items():
            assert getattr(addrs, field) == value


# get_addresses()

class TestGetAddresses:
    @pytest.mark.parametrize("chain_id,chain_name", [
        (1,     "MAINNET"),
        (137,   "POLYGON"),
        (10,    "OPTIMISM"),
        (42161, "ARBITRUM"),
    ])
    def test_returns_addresses_for_supported_chains(self, chain_id, chain_name):
        addrs = get_addresses(chain_id)
        assert isinstance(addrs, ProtocolAddresses)

    def test_mainnet_v2_factory(self):
        assert get_addresses(1).v2_factory == "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"

    def test_mainnet_weth(self):
        assert get_addresses(1).weth == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

    def test_polygon_v2_factory_differs_from_mainnet(self):
        assert get_addresses(1).v2_factory != get_addresses(137).v2_factory

    def test_unsupported_chain_raises_value_error(self):
        with pytest.raises(ValueError, match="not supported"):
            get_addresses(9999)

    def test_error_message_includes_supported_chains(self):
        with pytest.raises(ValueError) as exc_info:
            get_addresses(56)  # BSC — not supported
        message = str(exc_info.value)
        assert "1" in message or "137" in message

    def test_accepts_chain_id_enum(self):
        """get_addresses() works when passed a ChainId enum member."""
        assert get_addresses(ChainId.MAINNET).weth == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

    def test_all_chains_have_non_zero_weth(self):
        """Every registered chain has a valid WETH address."""
        for chain in ChainId:
            assert get_addresses(chain).weth != "0x0000000000000000000000000000000000000000"

    def test_all_chains_addresses_start_with_0x(self):
        """All address fields for every chain begin with '0x'."""
        for chain in ChainId:
            addrs = get_addresses(chain)
            for field, value in addrs.__dict__.items():
                assert value.startswith("0x"), (
                    f"Chain {chain.name} field '{field}' = '{value}' doesn't start with 0x"
                )

    def test_registry_covers_all_chain_ids(self):
        """_CHAIN_ADDRESSES has an entry for every ChainId member."""
        for chain in ChainId:
            assert chain in _CHAIN_ADDRESSES
