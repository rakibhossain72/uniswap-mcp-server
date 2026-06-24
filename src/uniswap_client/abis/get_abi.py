import json
from pathlib import Path
from typing import Dict, Optional

# Get the directory where this file is located
ABIS_DIR = Path(__file__).parent


def _load_abi(filename: str) -> Dict:
    """Load an ABI from a JSON file."""
    file_path = ABIS_DIR / filename
    with open(file_path, 'r') as f:
        return json.load(f)


# Individual ABI getter functions
def get_erc20_abi() -> Dict:
    """Get ERC20 ABI."""
    return _load_abi("ERC20_ABI.json")


def get_v2_factory_abi() -> Dict:
    """Get Uniswap V2 Factory ABI."""
    return _load_abi("V2_FACTORY_ABI.json")


def get_v2_pair_abi() -> Dict:
    """Get Uniswap V2 Pair ABI."""
    return _load_abi("V2_PAIR_ABI.json")


def get_v3_factory_abi() -> Dict:
    """Get Uniswap V3 Factory ABI."""
    return _load_abi("V3_FACTORY_ABI.json")


def get_v3_pool_abi() -> Dict:
    """Get Uniswap V3 Pool ABI."""
    return _load_abi("V3_POOL_ABI.json")


def get_v3_quoter_abi() -> Dict:
    """Get Uniswap V3 Quoter ABI."""
    return _load_abi("V3_QUOTER_ABI.json")


def get_v3_router_abi() -> Dict:
    """Get Uniswap V3 Router ABI."""
    return _load_abi("V3_ROUTER_ABI.json")


# Dictionary mapping for dynamic access
ABI_MAP = {
    "ERC20": get_erc20_abi,
    "V2_FACTORY": get_v2_factory_abi,
    "V2_PAIR": get_v2_pair_abi,
    "V3_FACTORY": get_v3_factory_abi,
    "V3_POOL": get_v3_pool_abi,
    "V3_QUOTER": get_v3_quoter_abi,
    "V3_ROUTER": get_v3_router_abi,
}
