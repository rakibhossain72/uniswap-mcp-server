import os
from mcp.server.fastmcp import FastMCP

from src.uniswap_client import UniswapClient

mcp = FastMCP("uniswap-mcp")

_client = None


def get_client() -> UniswapClient:
    global _client

    if _client is None:
        rpc_url = os.environ.get("RPC_URL")
        private_key = os.environ.get("PRIVATE_KEY")

        if not rpc_url:
            raise ValueError("RPC_URL environment variable is required")

        _client = UniswapClient(
            rpc_url=rpc_url,
            private_key=private_key,
        )

    return _client
