from fastmcp import FastMCP
import uvicorn

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

app = mcp.http_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
