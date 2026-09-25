from typing import Any, Optional

from ..app import mcp, run, split_uri
from ._annotations import READ


@mcp.tool(annotations=READ)
async def find_definition(uri: str, source: str, line: int, column: int) -> Optional[dict[str, Any]]:
    """Go to the definition of the identifier at line (1-based) / column (0-based).

    source is the current (possibly unsaved) source of uri. Returns the target's uri, line and column.
    """
    source_uri = split_uri(uri)[1]
    return await run(lambda c: c.find_definition(source_uri, source, line, column))


@mcp.tool(annotations=READ)
async def where_used(
    uri: str, line: Optional[int] = None, column: Optional[int] = None
) -> list[dict[str, Any]]:
    """Where-used list of an object, or of the element at line/column of a source URI (e.g. one method)."""
    return await run(lambda c: c.where_used(uri, line, column))


@mcp.tool(annotations=READ)
async def code_completion(uri: str, source: str, line: int, column: int) -> list[dict[str, Any]]:
    """Code completion proposals at line (1-based) / column (0-based) of the given source."""
    source_uri = split_uri(uri)[1]
    return await run(lambda c: c.code_completion(source_uri, source, line, column))
