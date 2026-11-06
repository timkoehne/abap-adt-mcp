from typing import Any

from ..app import mcp, run, split_uri
from ._annotations import READ


@mcp.tool(annotations=READ)
async def search_objects(query: str, max_results: int = 20) -> list[dict[str, Any]]:
    """Find objects by name, * is a wildcard (ZCL_*ORDER*).

    Returns type, name, description, package and uri of each hit. Other tools take this uri.
    """
    return await run(lambda c: c.search_object(query, max_results))


@mcp.tool(annotations=READ)
async def package_contents(package: str, recursive: bool = False) -> list[dict[str, Any]]:
    """Objects in a package. recursive=True includes subpackages."""
    return await run(lambda c: c.package_contents(package, recursive))


@mcp.tool(annotations=READ)
async def object_package_path(object_uri: str) -> list[dict[str, Any]]:
    """Package hierarchy of an object, top-level package first."""
    return await run(lambda c: c.object_package_path(split_uri(object_uri)[0]))


@mcp.tool(annotations=READ)
async def object_structure(object_uri: str) -> dict[str, Any]:
    """Outline of a class or interface: attributes, methods and types with their visibility."""
    return await run(lambda c: c.object_structure(split_uri(object_uri)[0]))
