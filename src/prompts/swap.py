from server import mcp


@mcp.prompt()
def execute_trade(token_in: str, token_out: str, amount: str) -> str:
    """Prompt to guide the AI safely through a token swap."""
    return f"""You have been asked to execute a trade: swapping {amount} of {token_in} for {token_out}.

Safety and precision are critical. Please follow these exact steps:
1. Use the `get_swap_quote` tool to check the expected output for this swap. Do NOT guess the price.
2. Present the returned quote to the user clearly, including the expected output amount and the fee tier used.
3. Ask the user for their explicit confirmation to proceed with the swap.
4. ONLY after the user confirms, use the `execute_swap` tool to perform the transaction on-chain.
5. Report the final transaction status to the user.
"""
