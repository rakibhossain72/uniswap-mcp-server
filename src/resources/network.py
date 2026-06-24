import asyncio
import json
from src.server import mcp, get_client

@mcp.resource("network://status")
async def get_network_status() -> str:
    """Get the current network status, including block number and chain ID."""
    client = get_client()
    
    def fetch_status():
        return {
            "chain_id": client.chain_id,
            "latest_block": client.w3.eth.block_number,
            "connected": client.w3.is_connected()
        }
        
    status = await asyncio.to_thread(fetch_status)
    return json.dumps(status, indent=2)
