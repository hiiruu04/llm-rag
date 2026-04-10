from loguru import logger
from mcp.server.fastmcp import FastMCP

from app.core.config import settings

mcp_server = FastMCP(
    "CMMS-MCP",
    instructions=(
        "MCP server for the CMMS (Computerized Maintenance Management System). "
        "Provides tools for querying assets, faults, sensors, maintenance schedules, "
        "and the Neo4j knowledge graph. Also provides resources for common CMMS views."
    ),
)


def create_mcp_app():
    """Create and configure the MCP server with all tools and resources."""
    if not settings.mcp_server_enabled:
        logger.info("MCP server is disabled")
        return None

    # Import tools and resources to register them with the FastMCP instance
    import app.mcp.resources.asset_resources  # noqa: F401
    import app.mcp.resources.fault_resources  # noqa: F401
    import app.mcp.resources.graph_resources  # noqa: F401
    import app.mcp.resources.maintenance_resources  # noqa: F401
    import app.mcp.resources.sensor_resources  # noqa: F401
    import app.mcp.tools.asset_tools  # noqa: F401
    import app.mcp.tools.fault_tools  # noqa: F401
    import app.mcp.tools.maintenance_tools  # noqa: F401
    import app.mcp.tools.query_tools  # noqa: F401
    import app.mcp.tools.sensor_tools  # noqa: F401

    logger.info("MCP server configured with tools and resources")
    return mcp_server
