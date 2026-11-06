from datetime import datetime, timedelta
from typing import Any, Optional

from ..app import mcp, run
from ._annotations import READ, WRITE


@mcp.tool(annotations=READ)
async def run_query(query: str, max_rows: int = 100) -> dict[str, Any]:
    """Run an ABAP SQL SELECT. Rows come back keyed by column name."""
    return await run(lambda c: c.run_query(query, max_rows))


@mcp.tool(annotations=WRITE)
async def run_class(class_name: str) -> str:
    """Run a class implementing IF_OO_ADT_CLASSRUN and return its console output."""
    return await run(lambda c: c.run_class(class_name))


@mcp.tool(annotations=READ)
async def list_dumps(
    user: Optional[str] = None,
    runtime_error: Optional[str] = None,
    since_hours: Optional[float] = None,
    max_results: int = 50,
) -> list[dict[str, Any]] | str:
    """Short dumps (ST22), newest first."""
    since = datetime.now() - timedelta(hours=since_hours) if since_hours else None
    return await run(lambda c: c.list_dumps(user, runtime_error, since, max_results)) or "No dumps found."


@mcp.tool(annotations=READ)
async def get_dump(dump_id: str) -> dict[str, Any]:
    """A short dump with its chapters."""
    return await run(lambda c: c.get_dump(dump_id))
