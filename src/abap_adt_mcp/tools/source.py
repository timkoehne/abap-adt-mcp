from typing import Any, Literal, Optional, Union

from ..app import mcp, object_name, run, split_uri, with_lock
from ._annotations import READ, WRITE


@mcp.tool(annotations=READ)
async def get_source(uri: str, version: Literal["active", "inactive"] = "active") -> str:
    """Source of an object, by the uri from search_objects.

    Parts of a class: <class uri>/includes/definitions, /implementations, /testclasses.
    TOP include of a function group: <group uri>/includes/l<group>top.
    version="inactive" returns saved changes that are not activated.
    """
    source_uri = split_uri(uri)[1]
    return await run(lambda c: c.get_object_source(source_uri, version))


@mcp.tool(annotations=WRITE)
async def write_source(
    uri: str, source: str, transport: Optional[str] = None, activate: bool = True
) -> str:
    """Replace the whole source at a uri (as in get_source) and activate the object.

    With activate=False it is only saved. Activation errors come with line numbers, and the
    source stays saved inactive.
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
async def activate(object_uris: Union[str, list[str]]) -> str:
    """Activate objects. Objects that depend on each other have to be activated in one call."""
    if isinstance(object_uris, str):
        object_uris = [object_uris]
    objects = [(object_name(uri), uri) for uri in (split_uri(uri)[0] for uri in object_uris)]
    await run(lambda c: c.activate_objects(objects))
    return "Activated " + ", ".join(name for name, _ in objects)


@mcp.tool(annotations=READ)
async def list_inactive_objects() -> list[dict[str, Any]]:
    """Objects of all users that are saved but not active."""
    return await run(lambda c: c.inactive_objects())


@mcp.tool(annotations=READ)
async def pretty_print(source: str) -> str:
    """Format ABAP source."""
    return await run(lambda c: c.prettyprint(source))
