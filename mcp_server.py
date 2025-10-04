from fastmcp import FastMCP
import uvicorn

mcp = FastMCP("Assistant tools")

@mcp.tool
def greet(name: str) -> str:
    """Greet a person by name"""
    return f"Hello, {name}!"

app = mcp.http_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
