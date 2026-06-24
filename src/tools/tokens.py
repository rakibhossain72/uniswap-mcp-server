from src.server import mcp, get_client
import asyncio

@mcp.tool()
async def get_token_info(token_address: str):
    """
    Get basic information about an ERC20 token, including its name, symbol, decimals, and total supply.
    """
    client = get_client()

    def fetch_info():
        return {
            "address": token_address,
            "name": client.erc20.name(token_address),
            "symbol": client.erc20.symbol(token_address),
            "decimals": client.erc20.decimal(token_address),
            "total_supply": str(client.erc20.total_supply(token_address))
        }

    return await asyncio.to_thread(fetch_info)
