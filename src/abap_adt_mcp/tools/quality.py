from typing import Any, Literal, Optional, Union

from abap_adt_py.api.unittest import UnittestFlags

from ..app import mcp, run, split_uri
from ._annotations import READ

_RISK_LEVELS = ["harmless", "dangerous", "critical"]
_DURATIONS = ["short", "medium", "long"]


@mcp.tool(annotations=READ)
async def syntax_check(
    uri: str, source: str, version: Literal["active", "inactive"] = "active"
) -> list[dict[str, Any]]:
    """Check source code for syntax errors without saving it. uri is the object or include the source belongs to.

    Returns the messages with type (E error, W warning), text, line and offset; empty if clean.
    """
    object_uri, source_uri = split_uri(uri)
    return await run(lambda c: c.syntax_check(object_uri, source_uri, source, version))


@mcp.tool(annotations=READ)
async def run_unit_tests(
    object_uri: str,
    max_risk_level: Literal["harmless", "dangerous", "critical"] = "harmless",
    max_duration: Literal["short", "medium", "long"] = "medium",
) -> list[dict[str, Any]]:
    """Run the ABAP unit tests of an object (class, program, package, ...).

    Returns the failed tests and warnings with their stack; an empty list means all tests passed.
    """
    risk = _RISK_LEVELS.index(max_risk_level)
    duration = _DURATIONS.index(max_duration)
    flags = UnittestFlags(
        harmless=True,
        dangerous=risk >= 1,
        critical=risk >= 2,
        short=True,
        medium=duration >= 1,
        long=duration >= 2,
    )
    object_uri = split_uri(object_uri)[0]
    return await run(lambda c: c.run_unit_test(object_uri, flags))


@mcp.tool(annotations=READ)
async def run_atc(
    object_uris: Union[str, list[str]],
    check_variant: Optional[str] = None,
    max_findings: int = 100,
) -> dict[str, Any]:
    """Run the ABAP Test Cockpit on objects or packages (the system's default variant unless given).

    Finding priority: 1 error, 2 warning, 3 information. Pass a finding's
    documentation_uri to atc_documentation for the explanation.
    """
    return await run(lambda c: c.run_atc(object_uris, check_variant, max_findings))


@mcp.tool(annotations=READ)
async def list_check_variants(pattern: str = "*", max_results: int = 100) -> list[dict[str, Any]]:
    """ATC check variants matching a name pattern."""
    return await run(lambda c: c.list_check_variants(pattern, max_results))


@mcp.tool(annotations=READ)
async def atc_documentation(documentation_uri: str) -> str:
    """Explanation of an ATC finding as plain text."""
    return await run(lambda c: c.atc_documentation(documentation_uri))
