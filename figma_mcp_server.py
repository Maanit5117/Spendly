import os
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server for Figma
mcp = FastMCP("FigmaLocal")

FIGMA_API_BASE = "https://api.figma.com/v1"

def get_figma_headers():
    token = os.environ.get("FIGMA_PERSONAL_ACCESS_TOKEN") or os.environ.get("FIGMA_ACCESS_TOKEN")
    if not token:
        raise ValueError(
            "Figma access token not found. Please set FIGMA_PERSONAL_ACCESS_TOKEN "
            "in your environment variables or in the mcp_config.json env dictionary."
        )
    return {"X-Figma-Token": token}

@mcp.tool()
def get_figma_file(file_key: str) -> str:
    """
    Retrieve the full JSON tree metadata and structure for a Figma file.
    """
    try:
        headers = get_figma_headers()
    except ValueError as e:
        return str(e)
        
    url = f"{FIGMA_API_BASE}/files/{file_key}"
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=30.0)
            if response.status_code == 200:
                # Truncate content length if it exceeds limit for LLM context safety
                return response.text[:60000]
            else:
                return f"Figma API error (HTTP {response.status_code}): {response.text}"
    except Exception as e:
        return f"Network error connecting to Figma: {e}"

@mcp.tool()
def get_figma_nodes(file_key: str, node_ids: str) -> str:
    """
    Retrieve JSON design metadata for specific node ID(s) (comma-separated list).
    """
    try:
        headers = get_figma_headers()
    except ValueError as e:
        return str(e)
        
    url = f"{FIGMA_API_BASE}/files/{file_key}/nodes"
    params = {"ids": node_ids}
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params, timeout=30.0)
            if response.status_code == 200:
                return response.text[:60000]
            else:
                return f"Figma API error (HTTP {response.status_code}): {response.text}"
    except Exception as e:
        return f"Network error connecting to Figma: {e}"

@mcp.tool()
def get_figma_images(file_key: str, node_ids: str, scale: float = 1.0, format: str = "png") -> str:
    """
    Render specified Figma nodes to images (png, pdf, svg, jpg) and return their CDN URLs.
    """
    try:
        headers = get_figma_headers()
    except ValueError as e:
        return str(e)
        
    url = f"{FIGMA_API_BASE}/images/{file_key}"
    params = {
        "ids": node_ids,
        "scale": scale,
        "format": format
    }
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params, timeout=30.0)
            if response.status_code == 200:
                return response.text
            else:
                return f"Figma API error (HTTP {response.status_code}): {response.text}"
    except Exception as e:
        return f"Network error rendering Figma images: {e}"

@mcp.tool()
def get_figma_styles(file_key: str) -> str:
    """
    Retrieve styling definitions (colors, typography, grid specifications) from a Figma file.
    """
    try:
        headers = get_figma_headers()
    except ValueError as e:
        return str(e)
        
    url = f"{FIGMA_API_BASE}/files/{file_key}/styles"
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=30.0)
            if response.status_code == 200:
                return response.text[:60000]
            else:
                return f"Figma API error (HTTP {response.status_code}): {response.text}"
    except Exception as e:
        return f"Network error fetching Figma styles: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
