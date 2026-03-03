from mcp.server.fastmcp import FastMCP
import random

mcp = FastMCP(name ="Dice Roller")

@mcp.tool()
def roll_dice_random(n_dice: int) :
    """Roll `n_dice` number of 6-sided dice and return the results as a list."""
    return [random.randint(1, 6) for _ in range(n_dice)]

if __name__ == "__main__":
    mcp.run(transport = "streamable-http")