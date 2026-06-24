"""Main Uniswap Client that orchestrates all contract interactions."""

import time
from decimal import Decimal
from typing import Optional, Dict

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from src.uniswap_client.addresses import get_addresses
from src.uniswap_client.contracts import (
    ERC20,
    V2Factory,
    V2Pair,
    V3Factory,
    V3Pool,
    V3Quoter,
    V3Router,
)
from src.uniswap_client.abis import ERC20_ABI


class UniswapClient:
    """Main Uniswap client that orchestrates all contract interactions."""

    def __init__(self, rpc_url: str, private_key: Optional[str] = None):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        # Support PoA chains (Polygon, etc.)
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        self.private_key = private_key
        self.account = (
            self.w3.eth.account.from_key(private_key) if private_key else None
        )

        self.chain_id = self.w3.eth.chain_id

        # Initialize contract wrappers (will be set per chain)
        self.erc20 = ERC20(self.w3)
        self.v2_factory: Optional[V2Factory] = None
        self.v3_factory: Optional[V3Factory] = None
        self.v3_quoter: Optional[V3Quoter] = None
        self.v3_router: Optional[V3Router] = None

        # Cache for contract instances
        self._pool_cache: Dict[str, V3Pool] = {}
        self._pair_cache: Dict[str, V2Pair] = {}

    def _checksum(self, address: str) -> str:
        return self.w3.to_checksum_address(address)

    def _get_erc20(self) -> ERC20:
        """Get the ERC20 helper instance."""
        return self.erc20

    def _initialize_contracts(self, chain_id: int = 1):
        """Initialize contract wrappers for the given chain."""
        addrs = get_addresses(chain_id)

        self.v2_factory = V2Factory(self.w3, addrs.v2_factory)
        self.v3_factory = V3Factory(self.w3, addrs.v3_factory)
        self.v3_quoter = V3Quoter(self.w3, addrs.v3_quoter)
        self.v3_router = V3Router(self.w3, addrs.v3_router)

    def _get_v3_pool(self, pool_address: str) -> V3Pool:
        """Get or create a V3 pool wrapper."""
        pool_address = self._checksum(pool_address)
        if pool_address not in self._pool_cache:
            self._pool_cache[pool_address] = V3Pool(self.w3, pool_address)
        return self._pool_cache[pool_address]

    def _get_v2_pair(self, pair_address: str) -> V2Pair:
        """Get or create a V2 pair wrapper."""
        pair_address = self._checksum(pair_address)
        if pair_address not in self._pair_cache:
            self._pair_cache[pair_address] = V2Pair(self.w3, pair_address)
        return self._pair_cache[pair_address]

    def _token_info(self, address: str) -> dict:
        """Get token information including symbol and decimals."""
        address = self._checksum(address)
        erc20 = self._get_erc20()
        return {
            "address": address,
            "symbol": erc20.symbol(address),
            "decimals": erc20.decimal(address),
        }

    # Token price (V3 sqrtPriceX96 → USD)
    def get_token_price(self, token_address: str, chain_id: int = 1) -> dict:
        self._initialize_contracts(chain_id)
        addrs = get_addresses(chain_id)
        token_address = self._checksum(token_address)

        quote_tokens = [
            ("USDC", addrs.usdc, 6),
            ("USDT", addrs.usdt, 6),
            ("WETH", addrs.weth, 18),
        ]

        erc20 = self._get_erc20()
        token_decimals = erc20.decimal(token_address)
        token_symbol = erc20.symbol(token_address)

        for fee in [500, 3000, 10000]:
            for quote_name, quote_addr, quote_decimals in quote_tokens:
                try:
                    pool_addr = self.v3_factory.get_pool(token_address, quote_addr, fee)
                    if pool_addr == "0x0000000000000000000000000000000000000000":
                        continue

                    pool = self._get_v3_pool(pool_addr)
                    slot0 = pool.slot0()
                    sqrt_price_x96 = slot0[0]

                    if sqrt_price_x96 == 0:
                        continue

                    token0_addr = pool.token0()
                    price_raw = (sqrt_price_x96 / (2**96)) ** 2

                    # Adjust for decimals
                    decimal_adj = 10 ** (token_decimals - quote_decimals)
                    if token0_addr.lower() == token_address.lower():
                        price_in_quote = price_raw / decimal_adj
                    else:
                        price_in_quote = (1 / price_raw) / decimal_adj

                    # WETH price needs USD conversion
                    if quote_name == "WETH":
                        weth_usd = self._get_weth_usd_price(chain_id)
                        usd_price = price_in_quote * weth_usd
                    else:
                        usd_price = price_in_quote

                    return {
                        "token": token_symbol,
                        "address": token_address,
                        "price_usd": round(float(usd_price), 8),
                        "quote_token": quote_name,
                        "fee_tier": fee,
                        "pool_address": pool_addr,
                        "chain_id": chain_id,
                    }

                except Exception:
                    continue

        return {"error": f"No V3 pool found for {token_symbol} on chain {chain_id}"}

    def _get_weth_usd_price(self, chain_id: int) -> float:
        self._initialize_contracts(chain_id)
        addrs = get_addresses(chain_id)

        for fee in [500, 3000]:
            try:
                pool_addr = self.v3_factory.get_pool(addrs["weth"], addrs["usdc"], fee)
                if pool_addr == "0x0000000000000000000000000000000000000000":
                    continue

                pool = self._get_v3_pool(pool_addr)
                slot0 = pool.slot0()
                sqrt_price = slot0[0] / (2**96)
                price_raw = sqrt_price**2
                token0 = pool.token0()

                if token0.lower() == addrs["weth"].lower():
                    return float(price_raw * 10**12)  # 18 - 6 decimals
                else:
                    return float((1 / price_raw) / 10**12)
            except Exception:
                continue
        return 3000.0  # fallback if all pools fail

    # V3 Pool
    def get_v3_pool(
        self, token0: str, token1: str, fee: int = 3000, chain_id: int = 1
    ) -> dict:
        self._initialize_contracts(chain_id)
        addrs = get_addresses(chain_id)

        pool_addr = self.v3_factory.get_pool(token0, token1, fee)

        if pool_addr == "0x0000000000000000000000000000000000000000":
            return {"error": f"No V3 pool found for tokens with fee {fee}"}

        return self.get_pool_by_address(pool_addr, chain_id)

    def get_pool_by_address(self, pool_address: str, chain_id: int = 1) -> dict:
        pool = self._get_v3_pool(pool_address)

        slot0 = pool.slot0()
        liquidity = pool.liquidity()
        fee = pool.fee()
        token0_addr = pool.token0()
        token1_addr = pool.token1()

        sqrt_price_x96 = slot0[0]
        current_tick = slot0[1]

        t0 = self._token_info(token0_addr)
        t1 = self._token_info(token1_addr)

        # Human-readable price (token1 per token0)
        price = 0.0
        if sqrt_price_x96 > 0:
            raw = (sqrt_price_x96 / (2**96)) ** 2
            decimal_adj = 10 ** (t0["decimals"] - t1["decimals"])
            price = float(raw / decimal_adj)

        return {
            "pool_address": pool_address,
            "chain_id": chain_id,
            "version": "v3",
            "token0": t0,
            "token1": t1,
            "fee_tier": fee,
            "fee_percent": f"{fee / 10000:.4f}%",
            "liquidity": str(liquidity),
            "sqrt_price_x96": str(sqrt_price_x96),
            "current_tick": current_tick,
            "price_token1_per_token0": round(price, 8),
        }

    # V2 Pair
    def get_v2_pair(self, token0: str, token1: str, chain_id: int = 1) -> dict:
        self._initialize_contracts(chain_id)
        addrs = get_addresses(chain_id)

        pair_addr = self.v2_factory.get_pair(token0, token1)

        if pair_addr == "0x0000000000000000000000000000000000000000":
            return {"error": "No V2 pair found for these tokens"}

        pair = self._get_v2_pair(pair_addr)
        reserves = pair.get_reserves()
        t0_addr = pair.token0()
        t1_addr = pair.token1()

        t0 = self._token_info(t0_addr)
        t1 = self._token_info(t1_addr)

        reserve0 = reserves[0] / (10 ** t0["decimals"])
        reserve1 = reserves[1] / (10 ** t1["decimals"])
        price = reserve1 / reserve0 if reserve0 > 0 else 0

        return {
            "pair_address": pair_addr,
            "chain_id": chain_id,
            "version": "v2",
            "token0": t0,
            "token1": t1,
            "reserve0": round(reserve0, 6),
            "reserve1": round(reserve1, 6),
            "price_token1_per_token0": round(price, 8),
            "block_timestamp_last": reserves[2],
        }

    # Swap quote (V3 Quoter)
    def get_swap_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: str,
        fee: int = 3000,
        chain_id: int = 1,
    ) -> dict:
        self._initialize_contracts(chain_id)
        token_in = self._checksum(token_in)
        token_out = self._checksum(token_out)

        erc20 = self._get_erc20()
        decimals_in = erc20.decimal(token_in)
        decimals_out = erc20.decimal(token_out)
        symbol_in = erc20.symbol(token_in)
        symbol_out = erc20.symbol(token_out)

        amount_in_wei = int(Decimal(amount_in) * Decimal(10**decimals_in))

        amount_out_wei = self.v3_quoter.quote_exact_input_single(
            token_in, token_out, fee, amount_in_wei, 0
        )

        amount_out = Decimal(amount_out_wei) / Decimal(10**decimals_out)
        price = float(amount_out) / float(amount_in)

        return {
            "token_in": {"address": token_in, "symbol": symbol_in},
            "token_out": {"address": token_out, "symbol": symbol_out},
            "amount_in": float(amount_in),
            "amount_out": float(amount_out),
            "price": round(price, 8),
            "fee_tier": fee,
            "chain_id": chain_id,
        }

    # Execute swap (V3 Router)
    def execute_swap(
        self,
        token_in: str,
        token_out: str,
        amount_in: str,
        slippage_bps: int = 50,
        fee: int = 3000,
        deadline_minutes: int = 20,
        chain_id: int = 1,
    ) -> dict:
        if not self.account:
            return {"error": "PRIVATE_KEY is not set — required for executing swaps"}

        self._initialize_contracts(chain_id)
        addrs = get_addresses(chain_id)
        token_in = self._checksum(token_in)
        token_out = self._checksum(token_out)
        router_addr = self._checksum(addrs["v3_router"])

        erc20 = self._get_erc20()
        decimals_in = erc20.decimal(token_in)
        decimals_out = erc20.decimal(token_out)
        symbol_in = erc20.symbol(token_in)
        symbol_out = erc20.symbol(token_out)

        amount_in_wei = int(Decimal(amount_in) * Decimal(10**decimals_in))

        # Get quote for slippage calc
        expected_out = self.v3_quoter.quote_exact_input_single(
            token_in, token_out, fee, amount_in_wei, 0
        )
        min_out = int(expected_out * (10000 - slippage_bps) / 10000)

        # Approve router if needed
        approval_result = self._ensure_approval(token_in, router_addr, amount_in_wei)

        # Build swap params
        deadline = int(time.time()) + deadline_minutes * 60

        params = {
            "tokenIn": token_in,
            "tokenOut": token_out,
            "fee": fee,
            "recipient": self.account.address,
            "deadline": deadline,
            "amountIn": amount_in_wei,
            "amountOutMinimum": min_out,
            "sqrtPriceLimitX96": 0,
        }

        nonce = self.w3.eth.get_transaction_count(self.account.address)
        gas_price = self.w3.eth.gas_price

        tx_func = self.v3_router.exact_input_single(params)
        tx = tx_func.build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": gas_price,
                "gas": 300_000,
            }
        )

        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

        amount_out_human = float(Decimal(expected_out) / Decimal(10**decimals_out))

        return {
            "status": "success" if receipt["status"] == 1 else "failed",
            "tx_hash": tx_hash.hex(),
            "token_in": {"symbol": symbol_in, "amount": float(amount_in)},
            "token_out": {"symbol": symbol_out, "expected_amount": amount_out_human},
            "slippage_bps": slippage_bps,
            "gas_used": receipt["gasUsed"],
            "block_number": receipt["blockNumber"],
            "approval": approval_result,
        }

    def _ensure_approval(self, token_addr: str, spender: str, amount: int) -> str:
        token = self.w3.eth.contract(address=self._checksum(token_addr), abi=ERC20_ABI)
        allowance = token.functions.allowance(self.account.address, spender).call()

        if allowance >= amount:
            return "already_approved"

        nonce = self.w3.eth.get_transaction_count(self.account.address)
        approve_tx = token.functions.approve(
            spender, 2**256 - 1  # max approval
        ).build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": self.w3.eth.gas_price,
                "gas": 100_000,
            }
        )

        signed = self.w3.eth.account.sign_transaction(approve_tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        return f"approved (tx: {tx_hash.hex()})"
