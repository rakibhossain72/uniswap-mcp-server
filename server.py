import os
from mcp.server.fastmcp import FastMCP

from src.uniswap_client import UniswapClient

mcp = FastMCP("uniswap-mcp")

_client = None


from src.config import settings

def get_client() -> UniswapClient:
    global _client

    if _client is None:
        _client = UniswapClient(
            rpc_url=settings.rpc_url,
            private_key=settings.private_key,
        )

    return _client

# Import all modules so the @mcp decorators are executed and registered
import src.tools
import src.resources
import src.prompts
