from typing import Any, Literal, Optional, Union

from abap_adt_py.api.ddic import ReferenceKinds

from ..app import mcp, run
from ._annotations import READ, WRITE
from ._models import FieldLabels, FixedValue, LockParameter, LockTable, plain


@mcp.tool(annotations=WRITE)
async def create_domain(
    name: str,
    package: str,
    description: str,
    data_type: str,
    length: int,
    decimals: int = 0,
    output_length: int = 0,
    conversion_exit: str = "",
    sign: bool = False,
    lowercase: bool = False,
    value_table: str = "",
    fixed_values: Optional[list[FixedValue]] = None,
    transport: Optional[str] = None,
) -> str:
    """Create and activate a domain. data_type e.g. CHAR, NUMC, DEC.

    output_length 0 lets SAP calculate it.
    """
    await run(
        lambda c: c.create_domain(
            name,
            package,
            description,
            data_type,
            length,
            decimals,
            transport,
            output_length=output_length,
            conversion_exit=conversion_exit,
            sign=sign,
            lowercase=lowercase,
            value_table=value_table,
            fixed_values=plain(fixed_values),
        )
    )
    return f"Created and activated domain {name.upper()}"


@mcp.tool(annotations=READ)
async def get_domain(
    name: str, version: Optional[Literal["active", "inactive"]] = None
) -> dict[str, Any]:
    """A domain's type, length, output settings, value table and fixed values."""
    return await run(lambda c: c.get_domain(name, version))


@mcp.tool(annotations=WRITE)
async def update_domain(
    name: str,
    description: Optional[str] = None,
    data_type: Optional[str] = None,
    length: Optional[int] = None,
    decimals: Optional[int] = None,
    output_length: Optional[int] = None,
    conversion_exit: Optional[str] = None,
    sign: Optional[bool] = None,
    lowercase: Optional[bool] = None,
    value_table: Optional[str] = None,
    fixed_values: Optional[list[FixedValue]] = None,
    transport: Optional[str] = None,
) -> str:
    """Change a domain and activate it. Arguments left out stay; fixed_values replaces all, [] removes them."""
    await run(
        lambda c: c.update_domain(
            name,
            description=description,
            data_type=data_type,
            length=length,
            decimals=decimals,
            output_length=output_length,
            conversion_exit=conversion_exit,
            sign=sign,
            lowercase=lowercase,
            value_table=value_table,
            fixed_values=plain(fixed_values),
            transport=transport,
        )
    )
    return f"Updated and activated domain {name.upper()}"


@mcp.tool(annotations=WRITE)
async def create_data_element(
    name: str,
    package: str,
    description: str,
    domain: Optional[str] = None,
    data_type: Optional[str] = None,
    length: int = 0,
    decimals: int = 0,
    reference_to: Optional[str] = None,
    reference_kind: ReferenceKinds = "class",
    labels: Optional[FieldLabels] = None,
    search_help: str = "",
    search_help_parameter: str = "",
    parameter_id: str = "",
    transport: Optional[str] = None,
) -> str:
    """Create and activate a data element, typed by exactly one of: domain; data_type with length;
    reference_to (TYPE REF TO a class or interface, with reference_kind a dictionary or built-in type).
    """
    await run(
        lambda c: c.create_data_element(
            name,
            package,
            description,
            domain=domain,
            data_type=data_type,
            length=length,
            decimals=decimals,
            reference_to=reference_to,
            reference_kind=reference_kind,
            labels=labels.model_dump(exclude_none=True) if labels else None,
            search_help=search_help,
            search_help_parameter=search_help_parameter,
            parameter_id=parameter_id,
            transport=transport,
        )
    )
    return f"Created and activated data element {name.upper()}"


@mcp.tool(annotations=READ)
async def get_data_element(
    name: str, version: Optional[Literal["active", "inactive"]] = None
) -> dict[str, Any]:
    """A data element's type, field labels, search help and parameter ID."""
    return await run(lambda c: c.get_data_element(name, version))


@mcp.tool(annotations=WRITE)
async def update_data_element(
    name: str,
    description: Optional[str] = None,
    domain: Optional[str] = None,
    data_type: Optional[str] = None,
    length: Optional[int] = None,
    decimals: Optional[int] = None,
    reference_to: Optional[str] = None,
    reference_kind: ReferenceKinds = "class",
    labels: Optional[FieldLabels] = None,
    search_help: Optional[str] = None,
    search_help_parameter: Optional[str] = None,
    parameter_id: Optional[str] = None,
    transport: Optional[str] = None,
) -> str:
    """Change a data element and activate it. Arguments left out stay; labels changes only the labels given."""
    await run(
        lambda c: c.update_data_element(
            name,
            description=description,
            domain=domain,
            data_type=data_type,
            length=length,
            decimals=decimals,
            reference_to=reference_to,
            reference_kind=reference_kind,
            labels=labels.model_dump(exclude_none=True) if labels else None,
            search_help=search_help,
            search_help_parameter=search_help_parameter,
            parameter_id=parameter_id,
            transport=transport,
        )
    )
    return f"Updated and activated data element {name.upper()}"


@mcp.tool(annotations=WRITE)
async def create_lock_object(
    name: str,
    package: str,
    description: str,
    primary_table: str,
    lock_mode: Literal["E", "S", "X"] = "E",
    secondary_tables: Optional[list[LockTable]] = None,
    parameters: Optional[list[Union[str, LockParameter]]] = None,
    allow_rfc: bool = False,
    transport: Optional[str] = None,
) -> str:
    """Create and activate a lock object; activation generates ENQUEUE_<name> and DEQUEUE_<name>.

    name starts with EZ. lock_mode: E write lock, S shared, X exclusive (not cumulative).
    parameters: the lock arguments, field names of the primary table or {name, table, field};
    left out, the primary table's key fields. In ABAP for Cloud Development use the lock object
    through cl_abap_lock_object_factory. Its uri is /sap/bc/adt/ddic/lockobjects/sources/<name>.
    """
    arguments = (
        [p if isinstance(p, str) else p.model_dump(exclude_none=True) for p in parameters]
        if parameters is not None
        else None
    )
    await run(
        lambda c: c.create_lock_object(
            name, package, description, primary_table, lock_mode, plain(secondary_tables), arguments,
            allow_rfc, transport,
        )
    )
    return f"Created and activated lock object {name.upper()} (ENQUEUE_{name.upper()}, DEQUEUE_{name.upper()})"


@mcp.tool(annotations=READ)
async def get_lock_object(name: str) -> dict[str, Any]:
    """A lock object's primary and secondary tables, lock modes, lock parameters and function modules."""
    return await run(lambda c: c.get_lock_object(name))
