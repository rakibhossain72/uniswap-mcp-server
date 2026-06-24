import os
from mcp.server.fastmcp import FastMCP

from src.config import settings
from src.uniswap_client import UniswapClient

mcp = FastMCP("uniswap-mcp")

_client = None


def get_client():
    """Return the singleton UniswapClient, initialising it on first call."""
    global _client

    if _client is None:
        # Deferred imports — only executed when the first tool/resource is called,
        # not at module load time.  This ensures all @mcp decorators register
        # successfully even before the RPC connection is validated.

        _client = UniswapClient(
            rpc_url=settings.rpc_url,
            private_key=settings.private_key,
        )

    return _client


# Import tool/resource/prompt modules so their @mcp decorators execute and
# register with the FastMCP instance above.  These imports must come after
# `mcp` is defined, but they contain no network calls themselves.
import src.tools
import src.resources
import src.prompts
