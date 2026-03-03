from mcp.server.fastmcp import FastMCP
import random

mcp = FastMCP("Random Number Generator")

@mcp.tool()
async def get_number(number: str):
    """Generate a random number """
    return random.randint(1, 100)

if __name__ == "__main__":
    mcp.run(transport="stdio")
