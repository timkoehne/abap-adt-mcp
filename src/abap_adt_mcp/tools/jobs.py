"""Application jobs (catalog entries and templates) and application log objects."""

from typing import Any, Optional, Union

from ..app import mcp, run
from ._annotations import READ, WRITE
from ._models import LogSubobject, ValueRange, plain


@mcp.tool(annotations=WRITE)
async def create_job_catalog_entry(
    name: str,
    package: str,
    description: str,
    class_name: str,
    parameters: Optional[list[dict[str, Any]]] = None,
    transport: Optional[str] = None,
) -> str:
    """Create and activate an application job catalog entry for an active class implementing
    IF_APJ_DT_EXEC_OBJECT and IF_APJ_RT_EXEC_OBJECT. The class's parameters are added by SAP;
    parameters only sets screen settings, e.g. [{"name": "P_ID", "mandatory": true}].
    Its uri is /sap/bc/adt/applicationjob/catalogs/<name>.
    """
    await run(
        lambda c: c.create_job_catalog_entry(name, package, description, class_name, parameters, transport)
    )
    return f"Created and activated job catalog entry {name.upper()}"


@mcp.tool(annotations=READ)
async def get_job_catalog_entry(name: str) -> dict[str, Any]:
    """An application job catalog entry's class and parameters."""
    entry = await run(lambda c: c.get_job_catalog_entry(name))
    return {key: value for key, value in entry.items() if key != "source"}


@mcp.tool(annotations=WRITE)
async def create_job_template(
    name: str,
    package: str,
    description: str,
    catalog_entry: str,
    parameters: Optional[dict[str, Union[str, list[ValueRange]]]] = None,
    transport: Optional[str] = None,
) -> str:
    """Create and activate an application job template for an active job catalog entry.

    parameters: values of the entry's parameters, a single value or a list of ranges, e.g.
    {"P_ID": "A1", "S_DATE": [{"sign": "I", "option": "BT", "low": "20250101", "high": "20251231"}]}.
    cl_apj_rt_api=>schedule_job schedules a job from it. Its uri is /sap/bc/adt/applicationjob/templates/<name>.
    """
    values = (
        {
            key: value if isinstance(value, str) else plain(value)
            for key, value in parameters.items()
        }
        if parameters
        else None
    )
    await run(lambda c: c.create_job_template(name, package, description, catalog_entry, values, transport))
    return f"Created and activated job template {name.upper()}"


@mcp.tool(annotations=READ)
async def get_job_template(name: str) -> dict[str, Any]:
    """An application job template's catalog entry and parameter values."""
    template = await run(lambda c: c.get_job_template(name))
    return {key: value for key, value in template.items() if key != "source"}


@mcp.tool(annotations=WRITE)
async def create_application_log_object(
    name: str,
    package: str,
    description: str,
    subobjects: Optional[list[LogSubobject]] = None,
    transport: Optional[str] = None,
) -> str:
    """Create and activate an application log object with subobjects; cl_bali_log writes logs for it.
    Its uri is /sap/bc/adt/applicationlog/objects/<name>.
    """
    await run(
        lambda c: c.create_application_log_object(name, package, description, plain(subobjects), transport)
    )
    return f"Created and activated application log object {name.upper()}"


@mcp.tool(annotations=READ)
async def get_application_log_object(name: str) -> dict[str, Any]:
    """An application log object's description and subobjects."""
    return await run(lambda c: c.get_application_log_object(name))
