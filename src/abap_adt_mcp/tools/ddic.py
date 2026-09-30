from typing import Any, Literal, Optional

from abap_adt_py.api.ddic import ReferenceKinds

from ..app import mcp, run
from ._annotations import READ, WRITE
from ._models import FieldLabels, FixedValue, plain


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
    """Create and activate a domain with its data type (e.g. CHAR, NUMC, DEC), length and decimals.

    output_length 0 lets SAP calculate it. fixed_values are single values
    ({"low": "N", "text": "New"}) or intervals ({"low": "1", "high": "9", "text": ...}).
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
    """A domain's data type, length, output characteristics, value table and fixed values."""
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
    """Change a domain and activate it. Arguments left out keep their value.

    fixed_values replaces all fixed values, [] removes them.
    """
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
    """Create and activate a data element, typed by exactly one of domain, data_type or reference_to.

    domain="ZSTATUS"; a built-in type data_type="CHAR", length=10; or TYPE REF TO a
    class or interface (reference_to="ZCL_FOO"), a dictionary type
    (reference_kind="dictionary") or a built-in type (reference_to="STRING",
    reference_kind="built_in").
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
    """A data element's type (type_kind, type_name, data_type), field labels, search help and parameter ID."""
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
    """Change a data element and activate it. Arguments left out keep their value.

    Passing domain, data_type or reference_to changes the type; labels only changes
    the labels it contains.
    """
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
