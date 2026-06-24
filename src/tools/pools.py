from server import mcp, get_client
import asyncio

@mcp.tool()
async def get_v3_pool(
    token0: str,
    token1: str,
    fee: int = 3000,
):
    """
    Fetch Uniswap V3 pool details.
    """

    client = get_client()

    return await asyncio.to_thread(
        client.get_v3_pool,
        token0=token0,
        token1=token1,
        fee=fee,
        chain_id=client.chain_id,
    )


@mcp.tool()
async def get_v2_pair(
    token0: str,
    token1: str,
):
    """
    Fetch Uniswap V2 pair details.
    """

    client = get_client()

    return await asyncio.to_thread(
        client.get_v2_pair,
        token0=token0,
        token1=token1,
        chain_id=client.chain_id,
    )


@mcp.tool()
async def get_pool_by_address(
    pool_address: str,
):
    """
    Fetch Uniswap V3 pool data by pool address.
    """

    client = get_client()

    return await asyncio.to_thread(
        client.get_pool_by_address,
        pool_address=pool_address,
        chain_id=client.chain_id,
    )
