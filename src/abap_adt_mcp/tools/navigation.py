from typing import Any, Optional

from ..app import mcp, run, split_uri
from ._annotations import READ


@mcp.tool(annotations=READ)
async def find_definition(uri: str, source: str, line: int, column: int) -> Optional[dict[str, Any]]:
    """Find the definition of the identifier at line (1-based) and column (0-based).

    source is the current source of uri, saved or not.
    """
    source_uri = split_uri(uri)[1]
    return await run(lambda c: c.find_definition(source_uri, source, line, column))


@mcp.tool(annotations=READ)
async def where_used(
    uri: str, line: Optional[int] = None, column: Optional[int] = None
) -> list[dict[str, Any]] | str:
    """Where an object is used, or the element at line and column of its source."""
    return await run(lambda c: c.where_used(uri, line, column)) or "Not used anywhere."


@mcp.tool(annotations=READ)
async def code_completion(uri: str, source: str, line: int, column: int) -> list[dict[str, Any]]:
    """Completion proposals at line (1-based) and column (0-based) of source."""
    source_uri = split_uri(uri)[1]
    return await run(lambda c: c.code_completion(source_uri, source, line, column))
