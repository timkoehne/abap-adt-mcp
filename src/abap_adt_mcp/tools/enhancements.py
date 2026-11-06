from typing import Any, Optional

from ..app import mcp, run
from ._annotations import READ, WRITE
from ._models import BadiImplementation, plain


@mcp.tool(annotations=READ)
async def get_enhancement_spot(name: str) -> dict[str, Any]:
    """An enhancement spot's BAdI definitions: interface, single or multiple use, fallback class, filters."""
    return await run(lambda c: c.get_enhancement_spot(name))


@mcp.tool(annotations=READ)
async def get_enhancement_implementation(name: str) -> dict[str, Any]:
    """An enhancement implementation's spot and BAdI implementations."""
    return await run(lambda c: c.get_enhancement_implementation(name))


@mcp.tool(annotations=WRITE)
async def create_enhancement_implementation(
    name: str,
    package: str,
    description: str,
    spot: str,
    implementations: list[BadiImplementation],
    transport: Optional[str] = None,
) -> str:
    """Create and activate an enhancement implementation of a spot's BAdIs.

    The implementing classes have to exist and implement the BAdI interface.
    Its uri is /sap/bc/adt/enhancements/enhoxhb/<name>.
    """
    await run(
        lambda c: c.create_enhancement_implementation(
            name, package, description, spot, plain(implementations), transport
        )
    )
    return f"Created and activated enhancement implementation {name.upper()}"


@mcp.tool(annotations=WRITE)
async def update_enhancement_implementation(
    name: str,
    implementations: Optional[list[BadiImplementation]] = None,
    description: Optional[str] = None,
    transport: Optional[str] = None,
) -> str:
    """Change an enhancement implementation and activate it. implementations replaces all of them."""
    await run(
        lambda c: c.update_enhancement_implementation(
            name, plain(implementations), description, transport
        )
    )
    return f"Updated and activated enhancement implementation {name.upper()}"
