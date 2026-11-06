from typing import Any, Optional

from ..app import mcp, run
from ._annotations import READ, WRITE


@mcp.tool(annotations=WRITE)
async def create_authorization_field(
    name: str,
    package: str,
    data_element: str,
    check_table: str = "",
    transport: Optional[str] = None,
) -> str:
    """Create an authorization field (SU20) typed by a data element with a domain.

    check_table holds the allowed values. Its uri is /sap/bc/adt/aps/iam/auth/<name>.
    """
    await run(
        lambda c: c.create_authorization_field(name, package, data_element, check_table, transport)
    )
    return f"Created authorization field {name.upper()}"


@mcp.tool(annotations=READ)
async def get_authorization_field(name: str) -> dict[str, Any]:
    """An authorization field's data element, check table, description and package."""
    return await run(lambda c: c.get_authorization_field(name))


@mcp.tool(annotations=WRITE)
async def update_authorization_field(
    name: str,
    data_element: Optional[str] = None,
    check_table: Optional[str] = None,
    transport: Optional[str] = None,
) -> str:
    """Change an authorization field. Arguments left out stay; check_table="" removes it."""
    await run(lambda c: c.update_authorization_field(name, data_element, check_table, transport))
    return f"Updated authorization field {name.upper()}"


@mcp.tool(annotations=WRITE)
async def create_authorization_object(
    name: str,
    package: str,
    description: str,
    fields: list[str],
    activities: Optional[list[str]] = None,
    object_class: str = "AAAB",
    transport: Optional[str] = None,
) -> str:
    """Create an authorization object (SU21) with up to 10 authorization fields.

    activities are the allowed ACTVT values when ACTVT is a field. object_class AAAB is
    cross-application. Its uri is /sap/bc/adt/aps/iam/suso/<name>.
    """
    await run(
        lambda c: c.create_authorization_object(
            name, package, description, object_class, fields, activities, transport
        )
    )
    return f"Created authorization object {name.upper()}"


@mcp.tool(annotations=READ)
async def get_authorization_object(name: str) -> dict[str, Any]:
    """An authorization object's class, fields, activities, description and package."""
    return await run(lambda c: c.get_authorization_object(name))


@mcp.tool(annotations=WRITE)
async def update_authorization_object(
    name: str,
    description: Optional[str] = None,
    fields: Optional[list[str]] = None,
    activities: Optional[list[str]] = None,
    object_class: Optional[str] = None,
    transport: Optional[str] = None,
) -> str:
    """Change an authorization object. Arguments left out stay; fields and activities are replaced."""
    await run(
        lambda c: c.update_authorization_object(
            name, description, object_class, fields, activities, transport
        )
    )
    return f"Updated authorization object {name.upper()}"
