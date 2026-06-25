from mcp.server.fastmcp import FastMCP
from src.config import settings
from src.uniswap_client import UniswapClient

# This is now the definitive single instance of your MCP server
mcp = FastMCP("uniswap-mcp")

_client = None

def get_client():
    """Return the singleton UniswapClient, initialising it on first call."""
    global _client

    if _client is None:
        _client = UniswapClient(
            rpc_url=settings.rpc_url,
            private_key=settings.private_key,
        )

    return _client