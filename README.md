# Uniswap MCP Server

A Model Context Protocol (MCP) server that exposes Uniswap V2 and V3 on-chain data and swap execution as tools, resources, and prompts. It connects any MCP-compatible AI client directly to the blockchain, allowing the model to query token prices, inspect liquidity pools, get swap quotes, and execute trades.

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [MCP Client Setup](#mcp-client-setup)
- [Supported Networks](#supported-networks)
- [Tools Reference](#tools-reference)
- [Resources Reference](#resources-reference)
- [Prompts Reference](#prompts-reference)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Security Considerations](#security-considerations)

---

## Overview

This server implements the [Model Context Protocol](https://modelcontextprotocol.io) using the FastMCP framework. When connected to an MCP client (such as Claude Desktop, Cursor, or any MCP-compatible agent), the AI model gains access to live Uniswap data without any custom integration code on the client side.

The server operates in two modes:

- **Read-only** — Query token info, pool data, and swap quotes. No private key required.
- **Read-write** — All of the above, plus the ability to execute on-chain swaps. Requires a funded wallet private key.

---

## Requirements

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An Ethereum-compatible RPC endpoint (Infura, Alchemy, a local node, or a public RPC)
- A funded wallet private key (only required for swap execution)

---

## Installation

Clone the repository and install dependencies.

```bash
git clone https://github.com/rakibhossain72/uniswap-mcp-server.git
cd uniswap-mcp-server
```

Using uv (recommended):

```bash
uv sync
```

Using pip:

```bash
pip install -e .
```

---

## Configuration

The server reads its configuration from environment variables. Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
# Required — your RPC endpoint URL
RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID

# Optional — required only for swap execution
PRIVATE_KEY=0xYOUR_PRIVATE_KEY

# Optional — default Uniswap V3 fee tier in bps (500, 3000, or 10000)
# Default: 3000 (0.3%)
DEFAULT_FEE_TIER=3000

# Optional — default slippage tolerance in basis points
# Default: 50 (0.5%)
DEFAULT_SLIPPAGE_BPS=50
```

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `RPC_URL` | Yes | — | RPC endpoint for the target network |
| `PRIVATE_KEY` | No | None | Wallet private key for executing swaps |
| `DEFAULT_FEE_TIER` | No | `3000` | Default V3 fee tier: `500`, `3000`, or `10000` |
| `DEFAULT_SLIPPAGE_BPS` | No | `50` | Slippage tolerance in basis points (50 = 0.5%) |

The server determines the network automatically from the `chain_id` reported by the RPC endpoint. To connect to Polygon, for example, set `RPC_URL` to a Polygon RPC URL.

---

## Running the Server

Start the server directly with uv:

```bash
uv run python server.py
```

Or using the MCP CLI:

```bash
uv run mcp run server.py
```

The server starts and listens for MCP client connections over stdio (the default transport).

---

## MCP Client Setup

### Claude Desktop

Add the following to your Claude Desktop configuration file.

On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`  
On Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "uniswap": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "/absolute/path/to/uniswap-mcp-server",
      "env": {
        "RPC_URL": "https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
        "PRIVATE_KEY": "0xYOUR_PRIVATE_KEY"
      }
    }
  }
}
```

Restart Claude Desktop after saving. The Uniswap tools will be available immediately in the next conversation.

### Cursor / VS Code

Add the server to your `.cursor/mcp.json` or workspace MCP settings:

```json
{
  "mcpServers": {
    "uniswap": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "/absolute/path/to/uniswap-mcp-server"
    }
  }
}
```

### Other MCP Clients

Any client that supports the MCP stdio transport can connect to this server. The command to run is:

```bash
uv run python server.py
```

from the project root directory, with `RPC_URL` available in the environment.

---

## Supported Networks

The server supports the following EVM networks. The active network is determined by the `RPC_URL` you configure.

| Network | Chain ID | Notes |
|---|---|---|
| Ethereum Mainnet | 1 | Full V2 and V3 support |
| Polygon | 137 | Full V2 and V3 support |
| Optimism | 10 | Full V2 and V3 support |
| Arbitrum One | 42161 | Full V2 and V3 support |

All protocol contract addresses (factory, quoter, router, WETH, USDC, USDT) are hardcoded per network and validated at startup.

---

## Tools Reference

Tools are callable functions exposed to the AI model. The model invokes them during a conversation to retrieve data or take action.

### get_token_info

Retrieve basic metadata for any ERC-20 token.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `token_address` | string | Checksummed ERC-20 contract address |

**Returns**

```json
{
  "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "name": "USD Coin",
  "symbol": "USDC",
  "decimals": 6,
  "total_supply": "45102345678901234"
}
```

---

### get_token_price

Get the real-time USD price of a token derived from on-chain Uniswap V3 pool data. The server tries USDC, USDT, and WETH quote pools across fee tiers (500, 3000, 10000) and returns the first valid result.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `token_address` | string | Checksummed ERC-20 contract address |

**Returns**

```json
{
  "token": "WETH",
  "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
  "price_usd": 3421.57,
  "quote_token": "USDC",
  "fee_tier": 500,
  "pool_address": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640",
  "chain_id": 1
}
```

If no pool is found for the token, the response includes an `error` key instead.

---

### get_v3_pool

Look up a Uniswap V3 pool by token pair and fee tier, then return its full on-chain state.

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `token0` | string | — | Address of the first token |
| `token1` | string | — | Address of the second token |
| `fee` | integer | `3000` | Fee tier: `500`, `3000`, or `10000` |

**Returns**

```json
{
  "pool_address": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640",
  "chain_id": 1,
  "version": "v3",
  "token0": { "address": "0xA0b8...", "symbol": "USDC", "decimals": 6 },
  "token1": { "address": "0xC02a...", "symbol": "WETH", "decimals": 18 },
  "fee_tier": 500,
  "fee_percent": "0.0500%",
  "liquidity": "12345678901234567890",
  "sqrt_price_x96": "1234567890123456789012345678",
  "current_tick": -197624,
  "price_token1_per_token0": 0.00029287
}
```

---

### get_v2_pair

Look up a Uniswap V2 pair by token addresses and return its reserves and implied price.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `token0` | string | Address of the first token |
| `token1` | string | Address of the second token |

**Returns**

```json
{
  "pair_address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
  "chain_id": 1,
  "version": "v2",
  "token0": { "address": "0xA0b8...", "symbol": "USDC", "decimals": 6 },
  "token1": { "address": "0xC02a...", "symbol": "WETH", "decimals": 18 },
  "reserve0": 45231890.123456,
  "reserve1": 13218.987654,
  "price_token1_per_token0": 0.00029231,
  "block_timestamp_last": 1718000000
}
```

---

### get_pool_by_address

Fetch full Uniswap V3 pool state directly by pool contract address, without needing the token pair.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `pool_address` | string | V3 pool contract address |

**Returns**

Same structure as `get_v3_pool`.

---

### get_swap_quote

Simulate a Uniswap V3 swap using the on-chain Quoter contract and return the expected output amount. No transaction is sent.

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `token_in` | string | — | Address of the token to sell |
| `token_out` | string | — | Address of the token to buy |
| `amount_in` | string | — | Human-readable input amount (e.g. `"1.5"`) |
| `fee` | integer | `3000` | Fee tier of the pool to route through |

**Returns**

```json
{
  "token_in": { "address": "0xA0b8...", "symbol": "USDC" },
  "token_out": { "address": "0xC02a...", "symbol": "WETH" },
  "amount_in": 1000.0,
  "amount_out": 0.29231,
  "price": 0.00029231,
  "fee_tier": 3000,
  "chain_id": 1
}
```

---

### execute_swap

Execute a Uniswap V3 swap on-chain. This tool sends a real transaction and requires `PRIVATE_KEY` to be configured. The router is approved automatically if the current allowance is insufficient.

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `token_in` | string | — | Address of the token to sell |
| `token_out` | string | — | Address of the token to buy |
| `amount_in` | string | — | Human-readable input amount (e.g. `"100"`) |
| `slippage_bps` | integer | `50` | Maximum acceptable slippage in basis points |
| `fee` | integer | `3000` | Fee tier of the pool to route through |
| `deadline_minutes` | integer | `20` | Transaction deadline in minutes from now |

**Returns**

```json
{
  "status": "success",
  "tx_hash": "0xabc123...",
  "token_in": { "symbol": "USDC", "amount": 1000.0 },
  "token_out": { "symbol": "WETH", "expected_amount": 0.29231 },
  "slippage_bps": 50,
  "gas_used": 142381,
  "block_number": 20000001,
  "approval": "already_approved"
}
```

If `PRIVATE_KEY` is not set, the tool returns immediately with:

```json
{
  "error": "PRIVATE_KEY is not set — required for executing swaps"
}
```

---

## Resources Reference

Resources are read-only data sources that the AI model can fetch at any point during a conversation.

### protocol://addresses

Returns the canonical protocol and token contract addresses for the currently connected chain.

**URI:** `protocol://addresses`

**Example response**

```json
{
  "v2_factory": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
  "v3_factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
  "v3_quoter": "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
  "v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
  "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
  "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "usdt": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  "chain_id": 1,
  "chain_name": "MAINNET"
}
```

---

### network://status

Returns the current connection state, chain ID, and latest block number.

**URI:** `network://status`

**Example response**

```json
{
  "chain_id": 1,
  "latest_block": 20123456,
  "connected": true
}
```

---

## Prompts Reference

Prompts are structured instruction templates that guide the AI model through multi-step workflows. They are invoked by name from a compatible MCP client.

### analyze_token

Guides the model through a full token analysis: fetches addresses, retrieves the USD price, inspects the V3 pool, and produces a summary report.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `token_address` | string | Address of the token to analyze |

**What the model does**

1. Reads `protocol://addresses` to get WETH and USDC addresses for the current chain.
2. Calls `get_token_price` to fetch the current USD price.
3. Calls `get_v3_pool` for the token paired against WETH and USDC at the 3000 fee tier.
4. Synthesizes a report covering price and pool liquidity.

---

### execute_trade

Guides the model through a safe, confirmation-gated swap workflow. The model will not send a transaction without explicit user approval.

**Parameters**

| Name | Type | Description |
|---|---|---|
| `token_in` | string | Symbol or address of the token to sell |
| `token_out` | string | Symbol or address of the token to buy |
| `amount` | string | Human-readable amount to sell |

**What the model does**

1. Calls `get_swap_quote` and presents the result to the user.
2. Asks for explicit user confirmation before proceeding.
3. Calls `execute_swap` only after confirmation is received.
4. Reports the final transaction status.

---

## Project Structure

```
uniswap-mcp-server/
├── server.py                        # FastMCP server entry point and client singleton
├── pyproject.toml                   # Project metadata and dependencies
├── .env                             # Local environment variables (not committed)
├── src/
│   ├── config.py                    # Pydantic config model, loaded from environment
│   ├── tools/
│   │   ├── pools.py                 # get_v3_pool, get_v2_pair, get_pool_by_address
│   │   ├── prices.py                # get_token_price
│   │   ├── swaps.py                 # get_swap_quote, execute_swap
│   │   └── tokens.py                # get_token_info
│   ├── resources/
│   │   ├── addresses.py             # protocol://addresses resource
│   │   └── network.py               # network://status resource
│   ├── prompts/
│   │   ├── analyze.py               # analyze_token prompt
│   │   └── swap.py                  # execute_trade prompt
│   └── uniswap_client/
│       ├── addresses.py             # Chain address registry and ChainId enum
│       ├── core/
│       │   └── client.py            # UniswapClient — orchestrates all contract calls
│       ├── contracts/
│       │   ├── base.py              # BaseContract
│       │   ├── erc20.py             # ERC-20 wrapper
│       │   ├── v2_factory.py        # Uniswap V2 Factory
│       │   ├── v2_pair.py           # Uniswap V2 Pair
│       │   ├── v3_factory.py        # Uniswap V3 Factory
│       │   ├── v3_pool.py           # Uniswap V3 Pool
│       │   ├── v3_quoter.py         # Uniswap V3 Quoter
│       │   └── v3_router.py         # Uniswap V3 Router
│       └── abis/                    # JSON ABI files for all contracts
└── tests/
    ├── conftest.py                  # Shared fixtures and address constants
    ├── test_abis.py
    ├── test_addresses.py
    ├── test_client.py
    ├── test_config.py
    ├── test_contracts.py
    ├── test_prompts.py
    ├── test_resources.py
    └── test_tools.py
```

---

## Running Tests

The test suite requires no network connection. All blockchain calls are mocked.

Install dev dependencies:

```bash
uv sync
```

Run the full suite:

```bash
uv run pytest tests/
```

Run a specific file:

```bash
uv run pytest tests/test_client.py
```

Run with verbose output:

```bash
uv run pytest tests/ -v
```

The suite covers 204 tests across configuration, address validation, ABI loading, all contract wrappers, the UniswapClient, every MCP tool, resource, and prompt.

---

## Security Considerations

**Private key handling.** The `PRIVATE_KEY` environment variable is read at startup and stored in memory for the lifetime of the server process. Never commit a `.env` file containing a real private key. Use a dedicated wallet with only the funds needed for the operations you intend to run.

**Token approvals.** `execute_swap` grants the V3 router an unlimited (`2^256 - 1`) token allowance if the current allowance is insufficient. This is standard practice for Uniswap interactions but means the router contract can spend that token on behalf of the wallet indefinitely. Revoke allowances manually if needed.

**Slippage.** The default slippage tolerance is 0.5% (`50` basis points). For low-liquidity tokens or large trade sizes, set a tighter slippage or verify the quote before confirming a swap.

**RPC endpoint trust.** The server trusts the data returned by the configured RPC URL. Use a reputable, authenticated endpoint rather than an unknown public RPC for any transaction-sending use case.

**Prompt confirmation gate.** The `execute_trade` prompt is designed to require explicit user confirmation before calling `execute_swap`. Do not bypass or modify this flow when using the server for live trading.
