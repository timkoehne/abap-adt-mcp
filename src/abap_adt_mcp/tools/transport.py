from typing import Any, Optional

from ..app import mcp, run, split_uri
from ._annotations import DESTRUCTIVE, READ, WRITE


@mcp.tool(annotations=READ)
async def transport_info(object_uri: str, package: str = "") -> dict[str, Any]:
    """Whether changing an object needs a transport request, and which requests can be used."""
    return await run(lambda c: c.transport_info(split_uri(object_uri)[0], package))


@mcp.tool(annotations=WRITE)
async def create_transport(object_uri: str, description: str, package: str) -> str:
    """Create a transport request for changes to an object in a package. Returns the request number."""
    return await run(lambda c: c.create_transport(split_uri(object_uri)[0], description, package))


@mcp.tool(annotations=READ)
async def list_transports(user: Optional[str] = None) -> list[dict[str, Any]]:
    """Modifiable transport requests of a user (default: the logged-in user) with tasks and objects."""
    return await run(lambda c: c.list_transports(user))


@mcp.tool(annotations=DESTRUCTIVE)
async def release_transport(transport: str) -> str:
    """Release a transport request (its tasks first). This cannot be undone."""
    await run(lambda c: c.release_transport(transport))
    return f"Released {transport}"


@mcp.tool(annotations=DESTRUCTIVE)
async def delete_transport(transport: str) -> str:
    """Delete a modifiable transport request."""
    await run(lambda c: c.delete_transport(transport))
    return f"Deleted {transport}"
