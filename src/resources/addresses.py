import json
from server import mcp, get_client
from src.uniswap_client.addresses import get_addresses, ChainId

@mcp.resource("protocol://addresses")
def get_protocol_addresses() -> str:
    """Get the Uniswap protocol and common token addresses for the current chain."""
    client = get_client()
    try:
        addrs = get_addresses(client.chain_id)
        # Convert dataclass to dict
        addr_dict = {k: v for k, v in addrs.__dict__.items() if not k.startswith('_')}
        addr_dict["chain_id"] = client.chain_id
        try:
            addr_dict["chain_name"] = ChainId(client.chain_id).name
        except ValueError:
            addr_dict["chain_name"] = "UNKNOWN"
        return json.dumps(addr_dict, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
