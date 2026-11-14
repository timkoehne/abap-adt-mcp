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
    language_version: Optional[Literal["standard", "cloudDevelopment", "keyUser"]] = None,
) -> str:
    """Create an empty object, then fill it with write_source.

    object_type: PROG/P report, PROG/I include, CLAS/OC class, INTF/OI interface, FUGR/F function
    group, FUGR/FF function module, TABL/DT table, TABL/DS structure, DDLS/DF CDS view, DDLX/EX
    metadata extension, DCLS/DL access control, SRVD/SRV service definition, BDEF/BDO behavior
    definition (named after its root CDS entity). Other types have their own create tools.
    package: $TMP for local objects; for a function module, its function group.
    language_version: ABAP language version, default standard; cloudDevelopment = ABAP for Cloud
    Development (not for reports, includes, function modules and message classes).
    """
    await run(
        lambda c: c.create(object_type, name, package, description, transport, language_version)
    )
    version = f" in {language_version}" if language_version else ""
    return f"Created {object_type} {name.upper()}{version}"


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
    """Create a package. Local packages start with $."""
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
    """Create and activate a table type of a dictionary row_type, or of a built-in data_type and length."""
    await run(
        lambda c: c.create_table_type(
            name, package, description, row_type, data_type, length, decimals, transport
        )
    )
    return f"Created and activated table type {name.upper()}"


@mcp.tool(annotations=WRITE)
async def create_test_class_include(class_name: str, transport: Optional[str] = None) -> str:
    """Add the include for local test classes to a class. Write it at <class uri>/includes/testclasses."""
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
    """Delete objects. Objects that use each other have to be deleted in one call."""
    if isinstance(object_uris, str) or len(object_uris) == 1:
        object_uri = split_uri(object_uris if isinstance(object_uris, str) else object_uris[0])[0]
        await run(
            lambda c: with_lock(c, object_uri, lambda handle: c.delete(object_uri, handle, transport))
        )
        return f"Deleted {object_uri}"
    uris = [split_uri(uri)[0] for uri in object_uris]
    await run(lambda c: c.delete_objects(uris, transport))
    return "Deleted " + ", ".join(uris)
