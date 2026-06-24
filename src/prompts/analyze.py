from src.server import mcp


@mcp.prompt()
def analyze_token(token_address: str) -> str:
    """Prompt to guide the AI in analyzing a specific token."""
    return f"""Please perform a comprehensive analysis of the token at address: {token_address}. 

Here is the step-by-step plan you should follow:
1. First, read the `protocol://addresses` resource to find the WETH and USDC addresses for the current connected chain.
2. Use the `get_token_price` tool to find the token's current USD price.
3. Use the `get_v3_pool` tool to fetch the Uniswap V3 pool details for the token against WETH and USDC (use the 3000 fee tier as a starting point).
4. Summarize your findings, providing the user with a report on the token's current price and its pool liquidity/parameters.
"""
