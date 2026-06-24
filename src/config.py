import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

class Config(BaseModel):
    """Application configuration for the Uniswap MCP Server."""
    
    rpc_url: str = Field(
        ..., 
        description="The RPC URL to connect to the blockchain (e.g., Infura, Alchemy, or public nodes)."
    )
    
    private_key: Optional[str] = Field(
        default=None, 
        description="Private key for executing transactions. Omit if you only want read-only access."
    )
    
    default_fee_tier: int = Field(
        default=3000, 
        description="Default Uniswap V3 fee tier (e.g., 500, 3000, 10000)."
    )
    
    default_slippage_bps: int = Field(
        default=50, 
        description="Default slippage tolerance in basis points (e.g., 50 = 0.5%)."
    )

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment variables with sensible defaults."""
        rpc_url = os.environ.get("RPC_URL")
        if not rpc_url:
            raise ValueError("RPC_URL environment variable is required to run the server.")

        return cls(
            rpc_url=rpc_url,
            private_key=os.environ.get("PRIVATE_KEY"),
            default_fee_tier=int(os.environ.get("DEFAULT_FEE_TIER", 3000)),
            default_slippage_bps=int(os.environ.get("DEFAULT_SLIPPAGE_BPS", 50))
        )

# Create a global configuration instance to be imported across the app
settings = Config.load()
