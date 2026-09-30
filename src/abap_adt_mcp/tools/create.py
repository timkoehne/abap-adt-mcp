from typing import Literal, Optional, Union

from abap_adt_py.api.create import ObjectTypes

from ..app import mcp, run, split_uri, with_lock
from ._annotations import DESTRUCTIVE, WRITE


@mcp.tool(annotations=WRITE)
async def create_object(
    object_type: ObjectTypes,
    name: str,
    package: str,
    description: str,
    transport: Optional[str] = None,
) -> str:
    """Create an empty repository object, then fill it with write_source.

    Types: PROG/P report, PROG/I include, CLAS/OC class, INTF/OI interface,
    FUGR/F function group, FUGR/FF function module (package = its function group),
    TABL/DT table, TABL/DS structure, DDLS/DF CDS view, DDLX/EX metadata extension,
    DCLS/DL access control, SRVD/SRV service definition, BDEF/BDO behavior definition (named after its root CDS entity).
    Domains, data elements, message classes, table types, service bindings and
    enhancement implementations have their own create tools.
    """
    await run(lambda c: c.create(object_type, name, package, description, transport))
    return f"Created {object_type} {name.upper()}"


@mcp.tool(annotations=WRITE)
async def create_package(
    name: str,
    description: str,
    parent: str = "",
    package_type: Literal["development", "structure", "main"] = "development",
    software_component: Optional[str] = None,
    transport_layer: str = "",
    transport: Optional[str] = None,
) -> str:
    """Create a package. Local packages start with $ (e.g. parent "$TMP"); others need a transport."""
    await run(
        lambda c: c.create_package(
            name, description, parent, package_type, software_component, transport_layer, transport
        )
    )
    return f"Created package {name.upper()}"


@mcp.tool(annotations=WRITE)
async def create_table_type(
    name: str,
    package: str,
    description: str,
    row_type: Optional[str] = None,
    data_type: Optional[str] = None,
    length: int = 0,
    decimals: int = 0,
    transport: Optional[str] = None,
) -> str:
    """Create and activate a table type, either of a dictionary row type (e.g. SCARR) or of a built-in data_type/length."""
    await run(
        lambda c: c.create_table_type(
            name, package, description, row_type, data_type, length, decimals, transport
        )
    )
    return f"Created and activated table type {name.upper()}"


@mcp.tool(annotations=WRITE)
async def create_test_class_include(class_name: str, transport: Optional[str] = None) -> str:
    """Add the local test class include to a class; write it via <class uri>/includes/testclasses."""
    class_uri = f"/sap/bc/adt/oo/classes/{class_name.lower()}"
    await run(
        lambda c: with_lock(
            c,
            class_uri,
            lambda handle: c.create_test_class_include(class_name, handle, transport),
        )
    )
    return f"Created test class include of {class_name.upper()}"


@mcp.tool(annotations=DESTRUCTIVE)
async def delete_object(object_uris: Union[str, list[str]], transport: Optional[str] = None) -> str:
    """Delete one or more objects from the system.

    Objects that use each other, e.g. a CDS root view and its composition child, have
    to be deleted together in one call.
    """
    if isinstance(object_uris, str) or len(object_uris) == 1:
        object_uri = split_uri(object_uris if isinstance(object_uris, str) else object_uris[0])[0]
        await run(
            lambda c: with_lock(c, object_uri, lambda handle: c.delete(object_uri, handle, transport))
        )
        return f"Deleted {object_uri}"
    uris = [split_uri(uri)[0] for uri in object_uris]
    await run(lambda c: c.delete_objects(uris, transport))
    return "Deleted " + ", ".join(uris)
