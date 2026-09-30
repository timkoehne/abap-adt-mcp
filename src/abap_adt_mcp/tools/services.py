from typing import Any, Literal, Optional

from ..app import mcp, run
from ._annotations import READ, WRITE


@mcp.tool(annotations=WRITE)
async def create_service_binding(
    name: str,
    package: str,
    description: str,
    service_definition: str,
    binding_type: str = "ODATA",
    version: str = "V4",
    category: Literal["ui", "web_api"] = "ui",
    transport: Optional[str] = None,
) -> str:
    """Create a service binding for a service definition (OData V4 UI by default).

    Activate it, then publish_service_binding makes the service callable.
    """
    await run(
        lambda c: c.create_service_binding(
            name, package, description, service_definition, binding_type, version, category, transport
        )
    )
    return f"Created service binding {name.upper()}"


@mcp.tool(annotations=READ)
async def get_service_binding(name: str) -> dict[str, Any]:
    """A service binding's type, version, category, whether it is published and its services with their URLs."""
    return await run(lambda c: c.get_service_binding(name))


@mcp.tool(annotations=WRITE)
async def publish_service_binding(name: str) -> list[str]:
    """Publish an activated OData V2 or V4 service binding locally. Returns the service URLs."""
    return await run(lambda c: c.publish_service_binding(name))


@mcp.tool(annotations=WRITE)
async def unpublish_service_binding(name: str) -> str:
    """Unpublish a service binding, its services are no longer callable."""
    await run(lambda c: c.unpublish_service_binding(name))
    return f"Unpublished {name.upper()}"
