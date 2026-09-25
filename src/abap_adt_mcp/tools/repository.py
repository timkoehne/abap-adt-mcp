from typing import Any

from ..app import mcp, run, split_uri
from ._annotations import READ


@mcp.tool(annotations=READ)
async def search_objects(query: str, max_results: int = 20) -> list[dict[str, Any]]:
    """Search repository objects by name, '*' is a wildcard (e.g. 'ZCL_*ORDER*').

    Every hit has the object's type, name, description, package and ADT URI.
    """
    return await run(lambda c: c.search_object(query, max_results))


@mcp.tool(annotations=READ)
async def package_contents(package: str, recursive: bool = False) -> list[dict[str, Any]]:
    """Objects in a package. Subpackages appear as DEVC/K entries; recursive=True descends into them."""
    return await run(lambda c: c.package_contents(package, recursive))


@mcp.tool(annotations=READ)
async def object_package_path(object_uri: str) -> list[dict[str, Any]]:
    """Package hierarchy of an object, top-level package first."""
    return await run(lambda c: c.object_package_path(split_uri(object_uri)[0]))


@mcp.tool(annotations=READ)
async def object_structure(object_uri: str) -> dict[str, Any]:
    """Outline of a class or interface: attributes, methods, types, ... with their visibility and links."""
    return await run(lambda c: c.object_structure(split_uri(object_uri)[0]))
