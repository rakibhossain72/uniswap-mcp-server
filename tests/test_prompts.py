"""
Tests for src/prompts/ — MCP prompt functions.

  - analyze_token   (src/prompts/analyze.py)
  - execute_trade   (src/prompts/swap.py)

Prompts are pure functions that return formatted strings — no blockchain
calls, no get_client usage.
"""

import pytest


# analyze_token

class TestAnalyzeToken:
    def _call(self, token_address: str) -> str:
        from src.prompts.analyze import analyze_token
        return analyze_token(token_address=token_address)

    def test_returns_string(self):
        assert isinstance(self._call("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"), str)

    def test_contains_token_address(self):
        addr = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        assert addr in self._call(addr)

    def test_references_get_token_price_tool(self):
        assert "get_token_price" in self._call("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

    def test_references_get_v3_pool_tool(self):
        assert "get_v3_pool" in self._call("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

    def test_references_protocol_addresses_resource(self):
        assert "protocol://addresses" in self._call("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

    def test_contains_numbered_steps(self):
        result = self._call("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
        for step in ("1.", "2.", "3.", "4."):
            assert step in result, f"Expected step '{step}' in analyze_token prompt"

    def test_different_addresses_produce_different_prompts(self):
        addr1 = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        addr2 = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
        assert self._call(addr1) != self._call(addr2)

    def test_prompt_is_non_empty(self):
        assert len(self._call("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2").strip()) > 0

    def test_prompt_mentions_weth_or_usdc(self):
        result = self._call("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
        assert "WETH" in result or "USDC" in result

    def test_prompt_mentions_liquidity_or_pool(self):
        lower = self._call("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2").lower()
        assert "liquidity" in lower or "pool" in lower


# execute_trade

class TestExecuteTrade:
    def _call(self, token_in: str, token_out: str, amount: str) -> str:
        from src.prompts.swap import execute_trade
        return execute_trade(token_in=token_in, token_out=token_out, amount=amount)

    def test_returns_string(self):
        assert isinstance(self._call("USDC", "WETH", "100"), str)

    def test_contains_token_in(self):
        assert "USDC" in self._call("USDC", "WETH", "100")

    def test_contains_token_out(self):
        assert "WETH" in self._call("USDC", "WETH", "100")

    def test_contains_amount(self):
        assert "250.5" in self._call("USDC", "WETH", "250.5")

    def test_references_get_swap_quote_tool(self):
        assert "get_swap_quote" in self._call("USDC", "WETH", "100")

    def test_references_execute_swap_tool(self):
        assert "execute_swap" in self._call("USDC", "WETH", "100")

    def test_contains_confirmation_step(self):
        lower = self._call("USDC", "WETH", "100").lower()
        assert "confirm" in lower or "confirmation" in lower

    def test_contains_numbered_steps(self):
        result = self._call("USDC", "WETH", "100")
        for step in ("1.", "2.", "3.", "4.", "5."):
            assert step in result, f"Expected step '{step}' in execute_trade prompt"

    def test_different_amounts_produce_different_prompts(self):
        assert self._call("USDC", "WETH", "100") != self._call("USDC", "WETH", "999")

    def test_different_pairs_produce_different_prompts(self):
        assert self._call("USDC", "WETH", "1") != self._call("WETH", "USDC", "1")

    def test_prompt_is_non_empty(self):
        assert len(self._call("USDC", "WETH", "1").strip()) > 0

    def test_prompt_warns_about_safety_or_precision(self):
        lower = self._call("USDC", "WETH", "1").lower()
        assert "safety" in lower or "precise" in lower or "critical" in lower
