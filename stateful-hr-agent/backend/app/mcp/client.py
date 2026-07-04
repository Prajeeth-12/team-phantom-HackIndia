from typing import Any, Awaitable, Callable, Dict

from app.mcp.servers.calendar_server import execute_calendar
from app.mcp.servers.docs_server import execute_docs
from app.mcp.servers.gmail_server import execute_gmail
from app.mcp.servers.postgres_server import execute_postgres

ServerAction = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


def _wrap(executor: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]], action: str) -> ServerAction:
    async def _run(payload: Dict[str, Any]) -> Dict[str, Any]:
        return await executor(action, payload)

    return _run


MCP_ACTIONS: Dict[str, Dict[str, ServerAction]] = {
    "postgres_mcp": {
        "get_candidates": _wrap(execute_postgres, "get_candidates"),
        "create_candidate": _wrap(execute_postgres, "create_candidate"),
        "update_candidate": _wrap(execute_postgres, "update_candidate"),
        "delete_candidate": _wrap(execute_postgres, "delete_candidate"),
    },
    "calendar_mcp": {
        "get_events": _wrap(execute_calendar, "get_events"),
        "create_event": _wrap(execute_calendar, "create_event"),
        "update_event": _wrap(execute_calendar, "update_event"),
        "cancel_event": _wrap(execute_calendar, "cancel_event"),
    },
    "gmail_mcp": {
        "send_email": _wrap(execute_gmail, "send_email"),
        "create_draft": _wrap(execute_gmail, "create_draft"),
    },
    "docs_mcp": {
        "create_document": _wrap(execute_docs, "create_document"),
        "update_document": _wrap(execute_docs, "update_document"),
    },
}

SERVER_ALIASES = {
    "postgres": "postgres_mcp",
    "postgres_mcp": "postgres_mcp",
    "calendar": "calendar_mcp",
    "calendar_mcp": "calendar_mcp",
    "gmail": "gmail_mcp",
    "gmail_mcp": "gmail_mcp",
    "docs": "docs_mcp",
    "docs_mcp": "docs_mcp",
}


class MCPClient:
    """
    Model Context Protocol (MCP) Client with strict registry-based action routing.
    """

    async def execute(self, server: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        server_key = SERVER_ALIASES.get((server or "").strip().lower(), (server or "").strip().lower())
        actions = MCP_ACTIONS.get(server_key)
        if not actions:
            return {"status": "error", "message": f"Unknown MCP server: {server}"}

        fn = actions.get((action or "").strip().lower())
        if not fn:
            return {
                "status": "error",
                "message": f"Unsupported action '{action}' for server '{server_key}'. Allowed: {sorted(actions.keys())}",
            }

        try:
            return await fn(payload or {})
        except Exception as e:
            return {"status": "error", "message": str(e)}


mcp_client = MCPClient()
