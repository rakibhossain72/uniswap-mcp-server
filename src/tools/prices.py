from src.server import mcp, get_client
import asyncio

@mcp.tool()
async def get_token_price(
    token_address: str,
):
    """
    Get the real-time price of a token in USD using Uniswap V3.
    Tries USDC, USDT, and WETH quote pools in order.
    """

    client = get_client()

    return await asyncio.to_thread(
        client.get_token_price,
        token_address=token_address,
        chain_id=client.chain_id,
    )
