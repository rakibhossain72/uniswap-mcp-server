"""
Tests for src/config.py — Config model and Config.load().

Design note: src/config.py calls load_dotenv() at module level (injecting .env
values into os.environ on import) and also instantiates a module-level
`settings` object.  To isolate Config.load() we:
  1. Mock load_dotenv to a no-op so it never injects .env values.
  2. Use patch.dict(os.environ, ...) to set exactly the env vars we want.
"""

import os
import pytest
from unittest.mock import patch


pytestmark = pytest.mark.usefixtures("_block_dotenv")


@pytest.fixture(autouse=True)
def _block_dotenv():
    """Prevent load_dotenv() from re-reading the .env file during any test."""
    with patch("src.config.load_dotenv", return_value=None):
        yield


def _load_with_env(**env_vars):
    """
    Call Config.load() with a precisely controlled environment.
    Strips all relevant keys then applies only what is passed.
    """
    from src.config import Config

    base = {k: v for k, v in os.environ.items()
            if k not in ("RPC_URL", "PRIVATE_KEY", "DEFAULT_FEE_TIER", "DEFAULT_SLIPPAGE_BPS")}
    base.update(env_vars)

    with patch.dict(os.environ, base, clear=True):
        return Config.load()


# Config.load()

class TestConfigLoad:
    def test_load_minimal_only_rpc_url(self):
        """Config.load() succeeds with only RPC_URL set; other fields use defaults."""
        cfg = _load_with_env(RPC_URL="http://localhost:8545")

        assert cfg.rpc_url == "http://localhost:8545"
        assert cfg.private_key is None
        assert cfg.default_fee_tier == 3000
        assert cfg.default_slippage_bps == 50

    def test_load_all_env_vars(self):
        """Config.load() reads every supported environment variable."""
        cfg = _load_with_env(
            RPC_URL="https://mainnet.infura.io/v3/abc",
            PRIVATE_KEY="0xdeadbeef",
            DEFAULT_FEE_TIER="500",
            DEFAULT_SLIPPAGE_BPS="100",
        )

        assert cfg.rpc_url == "https://mainnet.infura.io/v3/abc"
        assert cfg.private_key == "0xdeadbeef"
        assert cfg.default_fee_tier == 500
        assert cfg.default_slippage_bps == 100

    def test_load_raises_when_rpc_url_missing(self):
        """Config.load() raises ValueError when RPC_URL is not set."""
        with pytest.raises(ValueError, match="RPC_URL"):
            _load_with_env()

    def test_load_raises_when_rpc_url_empty_string(self):
        """Config.load() treats an empty RPC_URL as missing."""
        with pytest.raises(ValueError, match="RPC_URL"):
            _load_with_env(RPC_URL="")

    def test_default_fee_tier_is_3000(self):
        cfg = _load_with_env(RPC_URL="http://localhost:8545")
        assert cfg.default_fee_tier == 3000

    def test_default_slippage_bps_is_50(self):
        cfg = _load_with_env(RPC_URL="http://localhost:8545")
        assert cfg.default_slippage_bps == 50

    def test_custom_fee_tier_parsed_as_int(self):
        cfg = _load_with_env(RPC_URL="http://localhost:8545", DEFAULT_FEE_TIER="10000")
        assert cfg.default_fee_tier == 10000
        assert isinstance(cfg.default_fee_tier, int)

    def test_custom_slippage_bps_parsed_as_int(self):
        cfg = _load_with_env(RPC_URL="http://localhost:8545", DEFAULT_SLIPPAGE_BPS="200")
        assert cfg.default_slippage_bps == 200
        assert isinstance(cfg.default_slippage_bps, int)

    def test_private_key_absent_by_default(self):
        cfg = _load_with_env(RPC_URL="http://localhost:8545")
        assert cfg.private_key is None

    def test_private_key_set_when_env_present(self):
        cfg = _load_with_env(RPC_URL="http://localhost:8545", PRIVATE_KEY="0xsecretkey")
        assert cfg.private_key == "0xsecretkey"

    def test_fee_tier_500(self):
        assert _load_with_env(RPC_URL="http://localhost:8545", DEFAULT_FEE_TIER="500").default_fee_tier == 500

    def test_fee_tier_3000(self):
        assert _load_with_env(RPC_URL="http://localhost:8545", DEFAULT_FEE_TIER="3000").default_fee_tier == 3000

    def test_fee_tier_10000(self):
        assert _load_with_env(RPC_URL="http://localhost:8545", DEFAULT_FEE_TIER="10000").default_fee_tier == 10000


# Config model — direct instantiation and Pydantic validation

class TestConfigModel:
    def test_direct_instantiation(self):
        from src.config import Config
        cfg = Config(rpc_url="http://localhost:8545")
        assert cfg.rpc_url == "http://localhost:8545"

    def test_rpc_url_is_required(self):
        from src.config import Config
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Config()  # type: ignore[call-arg]

    def test_all_fields_explicit(self):
        from src.config import Config
        cfg = Config(
            rpc_url="http://node.example.com",
            private_key="0xabc",
            default_fee_tier=500,
            default_slippage_bps=25,
        )
        assert cfg.rpc_url == "http://node.example.com"
        assert cfg.private_key == "0xabc"
        assert cfg.default_fee_tier == 500
        assert cfg.default_slippage_bps == 25

    def test_model_is_pydantic_base_model(self):
        from src.config import Config
        from pydantic import BaseModel
        assert issubclass(Config, BaseModel)

    def test_private_key_defaults_to_none(self):
        from src.config import Config
        assert Config(rpc_url="http://localhost:8545").private_key is None

    def test_default_fee_tier_default(self):
        from src.config import Config
        assert Config(rpc_url="http://localhost:8545").default_fee_tier == 3000

    def test_default_slippage_bps_default(self):
        from src.config import Config
        assert Config(rpc_url="http://localhost:8545").default_slippage_bps == 50
