from app.core.config import settings


def validate_mcp_api_key(api_key: str | None) -> bool:
    """Validate the MCP API key. Returns True if valid or if no key is configured."""
    if not settings.mcp_api_key:
        return True  # No auth required
    return api_key == settings.mcp_api_key
