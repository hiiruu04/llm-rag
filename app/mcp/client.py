import json
from typing import Optional

from loguru import logger

from app.core.config import settings


class MCPServerConnection:
    def __init__(self, name: str, url: str, api_key: Optional[str] = None):
        self.name = name
        self.url = url
        self.api_key = api_key
        self.tools: list[dict] = []

    async def connect(self):
        """Discover available tools from the MCP server."""
        try:
            import httpx

            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-MCP-API-Key"] = self.api_key

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": 1,
                    },
                    headers=headers,
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("result", {})
                    self.tools = result.get("tools", [])
                    logger.info(
                        f"Connected to MCP server '{self.name}', "
                        f"found {len(self.tools)} tools"
                    )
                else:
                    logger.warning(
                        f"Failed to connect to MCP server '{self.name}': {response.status_code}"
                    )
        except Exception as e:
            logger.error(f"Error connecting to MCP server '{self.name}': {e}")

    async def call_tool(self, tool_name: str, arguments: dict) -> Optional[str]:
        """Call a tool on the MCP server."""
        try:
            import httpx

            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-MCP-API-Key"] = self.api_key

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments,
                        },
                        "id": 2,
                    },
                    headers=headers,
                    timeout=30.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("result", {})
                    content = result.get("content", [])
                    if content:
                        return content[0].get("text", "")
                    return json.dumps(result)
                else:
                    logger.error(
                        f"Tool call failed on '{self.name}': {response.status_code}"
                    )
                    return None
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}' on '{self.name}': {e}")
            return None


class MCPClientManager:
    def __init__(self):
        self.servers: list[MCPServerConnection] = []
        self._initialized = False

    async def initialize(self):
        """Connect to all configured MCP servers."""
        if self._initialized:
            return

        if not settings.mcp_client_enabled:
            logger.info("MCP client is disabled")
            self._initialized = True
            return

        try:
            servers_config = json.loads(settings.mcp_client_servers)
        except json.JSONDecodeError:
            logger.error("Invalid MCP_CLIENT_SERVERS JSON configuration")
            self._initialized = True
            return

        for server_cfg in servers_config:
            conn = MCPServerConnection(
                name=server_cfg.get("name", "unknown"),
                url=server_cfg.get("url", ""),
                api_key=server_cfg.get("api_key"),
            )
            if conn.url:
                await conn.connect()
                self.servers.append(conn)

        self._initialized = True
        logger.info(f"MCP client initialized with {len(self.servers)} servers")

    def get_all_tools(self) -> list[dict]:
        """Get all available tools from all connected servers."""
        tools = []
        for server in self.servers:
            for tool in server.tools:
                tools.append({
                    "server": server.name,
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "parameters": tool.get("inputSchema", {}),
                })
        return tools

    async def call_tool(self, tool_name: str, arguments: dict) -> Optional[str]:
        """Call a tool on the appropriate server."""
        for server in self.servers:
            for tool in server.tools:
                if tool.get("name") == tool_name:
                    return await server.call_tool(tool_name, arguments)
        logger.warning(f"Tool '{tool_name}' not found on any connected server")
        return None

    async def call_all_tools(self, tool_name: str, arguments: dict) -> list[str]:
        """Call a tool on all servers that have it. Returns list of results."""
        results = []
        for server in self.servers:
            for tool in server.tools:
                if tool.get("name") == tool_name:
                    result = await server.call_tool(tool_name, arguments)
                    if result:
                        results.append(result)
        return results


_mcp_client_manager: Optional[MCPClientManager] = None


async def get_mcp_client_manager() -> MCPClientManager:
    global _mcp_client_manager
    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager()
        await _mcp_client_manager.initialize()
    return _mcp_client_manager
