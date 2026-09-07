"""
Lab 3 - Secure MCP server (SKELETON)

A real Model Context Protocol server built with FastMCP, exposing three tools
over streamable HTTP on :8000. Add the security:
  1. Every tools/call must carry a valid Bearer JWT (verified with PyJWT)
  2. The call is allowed only if the token's scopes include tools:<name>
The scope check runs in FastMCP middleware, so every tool is protected by
default.

NOTE: incomplete. Merge in the enforce_scope() logic from
extra/secure_server_complete.txt before running.
"""
from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware
from fastmcp.server.dependencies import get_http_headers
from fastmcp.exceptions import ToolError
import auth   # provided: mint_token() / verify_token() with PyJWT


# ===========================================================================
#  HOW A TOOL CALL FLOWS THROUGH THIS SERVER
#
#      client  --tools/call-->  ScopeMiddleware.on_call_tool()
#                                 1. no Bearer token?        -> 401
#                                 2. token fails to verify?  -> 401
#                                 3. enforce_scope()         -> 403 if the
#                                    token lacks tools:<name>
#                               -> the tool itself runs only if all three pass
#
#  The middleware wraps EVERY tool, so a new tool is protected by default.
# ===========================================================================

# ---------------------------------------------------------------------------
#  AUTHENTICATION helpers (provided)
# ---------------------------------------------------------------------------
def _bearer(headers):
    """Pull the raw token out of an 'Authorization: Bearer ...' header."""
    value = headers.get("authorization", "")
    if value.lower().startswith("bearer "):
        return value[7:]
    return None


# ---------------------------------------------------------------------------
#  AUTHORIZATION - the one function you build: per-tool scope check
# ---------------------------------------------------------------------------
def enforce_scope(claims, tool_name):
    """Per-tool authorization: the token must carry the tools:<name> scope."""
    # TODO (merge): read scopes from claims; raise ToolError 403 if the token
    # does not include tools:<tool_name>.
    raise NotImplementedError("enforce_scope not implemented yet")


# ---------------------------------------------------------------------------
#  THE MIDDLEWARE (provided) - runs before every tools/call
# ---------------------------------------------------------------------------
class ScopeMiddleware(Middleware):
    """Authenticates the JWT and enforces per-tool scopes on every call."""

    async def on_call_tool(self, context, call_next):
        headers = get_http_headers(include={"authorization"})
        token = _bearer(headers)
        if token is None:
            raise ToolError("401 Unauthorized: missing bearer token")
        try:
            claims = auth.verify_token(token)
        except Exception as e:
            raise ToolError(f"401 Unauthorized: invalid token ({e})")

        enforce_scope(claims, context.message.name)
        print(f"[SECURE] {claims['sub']} -> {context.message.name} (allowed)")
        return await call_next(context)


# ---------------------------------------------------------------------------
#  THE SERVER + ITS TOOLS (provided) - nothing security-specific in here;
#  the middleware above protects all three tools
# ---------------------------------------------------------------------------
mcp = FastMCP("omnitech-calc")
mcp.add_middleware(ScopeMiddleware())


@mcp.tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@mcp.tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    return a / b


if __name__ == "__main__":
    print("[SECURE] FastMCP server on http://127.0.0.1:8000/mcp/")
    print("[SECURE] tools exposed: add, multiply, divide (scope-protected)")
    mcp.run(transport="http", host="127.0.0.1", port=8000)
