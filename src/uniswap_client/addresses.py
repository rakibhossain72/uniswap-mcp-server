from dataclasses import dataclass
from enum import IntEnum
from typing import Dict


class ChainId(IntEnum):
    """Supported EVM Chain IDs with friendly names."""

    MAINNET = 1
    POLYGON = 137
    OPTIMISM = 10
    ARBITRUM = 42161


@dataclass(frozen=True)
class ProtocolAddresses:
    """Read-only container for a chain's protocol and token addresses."""

    v2_factory: str
    v3_factory: str
    v3_quoter: str
    v3_router: str
    weth: str
    usdc: str
    usdt: str

    def __post_init__(self):
        """Basic validation to ensure addresses look like valid hex strings."""
        for field_name, value in self.__dict__.items():
            if (
                not isinstance(value, str)
                or not value.startswith("0x")
                or len(value) != 42
            ):
                raise ValueError(
                    f"Invalid Ethereum address format for {field_name}: '{value}'"
                )


# Internal registry using the defined structures
_CHAIN_ADDRESSES: Dict[ChainId, ProtocolAddresses] = {
    ChainId.MAINNET: ProtocolAddresses(
        v2_factory="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        v3_factory="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        v3_quoter="0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
        v3_router="0xE592427A0AEce92De3Edee1F18E0157C05861564",
        weth="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        usdc="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        usdt="0xdAC17F958D2ee523a2206206994597C13D831ec7",
    ),
    ChainId.POLYGON: ProtocolAddresses(
        v2_factory="0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
        v3_factory="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        v3_quoter="0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
        v3_router="0xE592427A0AEce92De3Edee1F18E0157C05861564",
        weth="0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        usdc="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        usdt="0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    ),
    ChainId.OPTIMISM: ProtocolAddresses(
        v2_factory="0x0c3c1c532F1e39EdF36BE9Fe0bE1410313E074Bf",
        v3_factory="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        v3_quoter="0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
        v3_router="0xE592427A0AEce92De3Edee1F18E0157C05861564",
        weth="0x4200000000000000000000000000000000000006",
        usdc="0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
        usdt="0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
    ),
    ChainId.ARBITRUM: ProtocolAddresses(
        v2_factory="0xf1D7CC64Fb4452F05c498126312eBE29f30Fbcf9",
        v3_factory="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        v3_quoter="0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
        v3_router="0xE592427A0AEce92De3Edee1F18E0157C05861564",
        weth="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        usdc="0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
        usdt="0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
    ),
}


def get_addresses(chain_id: int) -> ProtocolAddresses:
    """
    Retrieve addresses for a given chain ID.

    Raises:
        ValueError: If the chain ID is unsupported.
    """
    try:
        # Resolves raw ints or ChainId enums seamlessly
        target_chain = ChainId(chain_id)
        return _CHAIN_ADDRESSES[target_chain]
    except ValueError:
        supported = [c.value for c in ChainId]
        raise ValueError(
            f"Chain ID {chain_id} is not supported. Choose from {supported}"
        )
