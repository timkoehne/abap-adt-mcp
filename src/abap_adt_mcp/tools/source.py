from typing import Literal, Optional

from ..app import mcp, object_name, run, split_uri, with_lock
from ._annotations import READ, WRITE


@mcp.tool(annotations=READ)
async def get_source(uri: str, version: Literal["active", "inactive"] = "active") -> str:
    """Source code of an object (object URI) or of one of its includes (source URI).

    version="inactive" returns saved but not yet activated changes.
    """
    source_uri = split_uri(uri)[1]
    return await run(lambda c: c.get_object_source(source_uri, version))


@mcp.tool(annotations=WRITE)
async def write_source(
    uri: str, source: str, transport: Optional[str] = None, activate: bool = True
) -> str:
    """Replace the complete source code of an object or include and activate it.

    Locks the object, writes, unlocks again and activates unless activate=False.
    Activation errors are returned with line positions; the source stays saved inactive.
    Objects in transportable packages need a transport request number.
    """
    object_uri, source_uri = split_uri(uri)

    def write(c) -> str:
        with_lock(
            c,
            object_uri,
            lambda handle: c.set_object_source(source_uri, source, handle, transport),
        )
        if not activate:
            return f"Saved {source_uri} (inactive)"
        c.activate(object_name(object_uri), object_uri)
        return f"Saved and activated {object_name(object_uri)}"

    return await run(write)


@mcp.tool(annotations=WRITE)
async def activate(object_uri: str, name: Optional[str] = None) -> str:
    """Activate an object. The name defaults to the last segment of the URI."""
    object_uri = split_uri(object_uri)[0]
    name = name or object_name(object_uri)
    await run(lambda c: c.activate(name, object_uri))
    return f"Activated {name}"


@mcp.tool(annotations=READ)
async def pretty_print(source: str) -> str:
    """Format ABAP source with the system's pretty printer settings."""
    return await run(lambda c: c.prettyprint(source))
