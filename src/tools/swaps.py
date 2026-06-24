from server import mcp, get_client
import asyncio

@mcp.tool()
async def get_swap_quote(
    token_in: str,
    token_out: str,
    amount_in: str,
    fee: int = 3000,
):
    """
    Get a swap quote using Uniswap V3 Quoter.
    """

    client = get_client()

    return await asyncio.to_thread(
        client.get_swap_quote,
        token_in=token_in,
        token_out=token_out,
        amount_in=amount_in,
        fee=fee,
        chain_id=client.chain_id,
    )



@mcp.tool()
async def execute_swap(
    token_in: str,
    token_out: str,
    amount_in: str,
    slippage_bps: int = 50,
    fee: int = 3000,
    deadline_minutes: int = 20,
):
    """
    Execute a token swap on Uniswap V3.
    Requires PRIVATE_KEY.
    """

    client = get_client()

    return await asyncio.to_thread(
        client.execute_swap,
        token_in=token_in,
        token_out=token_out,
        amount_in=amount_in,
        slippage_bps=slippage_bps,
        fee=fee,
        deadline_minutes=deadline_minutes,
        chain_id=client.chain_id,
    )
