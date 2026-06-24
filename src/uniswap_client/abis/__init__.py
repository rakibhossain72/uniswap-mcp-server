"""
Uniswap contract ABIs.
"""

from .get_abi import (
    get_erc20_abi,
    get_v2_factory_abi,
    get_v2_pair_abi,
    get_v3_factory_abi,
    get_v3_pool_abi,
    get_v3_quoter_abi,
    get_v3_router_abi,
)


# Lazy loading - functions that return ABIs when called
def ERC20_ABI():
    return get_erc20_abi()


def V2_FACTORY_ABI():
    return get_v2_factory_abi()


def V2_PAIR_ABI():
    return get_v2_pair_abi()


def V3_FACTORY_ABI():
    return get_v3_factory_abi()


def V3_POOL_ABI():
    return get_v3_pool_abi()


def V3_QUOTER_ABI():
    return get_v3_quoter_abi()


def V3_ROUTER_ABI():
    return get_v3_router_abi()


__all__ = [
    "get_abi",
    "get_all_abis",
    "get_erc20_abi",
    "get_v2_factory_abi",
    "get_v2_pair_abi",
    "get_v3_factory_abi",
    "get_v3_pool_abi",
    "get_v3_quoter_abi",
    "get_v3_router_abi",
    "ERC20_ABI",
    "V2_FACTORY_ABI",
    "V2_PAIR_ABI",
    "V3_FACTORY_ABI",
    "V3_POOL_ABI",
    "V3_QUOTER_ABI",
    "V3_ROUTER_ABI",
]
