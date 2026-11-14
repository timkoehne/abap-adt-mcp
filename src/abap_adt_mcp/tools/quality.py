from typing import Any, Literal, Optional, Union

from abap_adt_py.api.unittest import UnittestFlags

from ..app import mcp, run, split_uri
from ._annotations import DESTRUCTIVE, READ, WRITE
from ._models import AtcCheckSetting, plain

_RISK_LEVELS = ["harmless", "dangerous", "critical"]
_DURATIONS = ["short", "medium", "long"]


@mcp.tool(annotations=READ)
async def syntax_check(
    uri: str, source: str, version: Literal["active", "inactive"] = "active"
) -> list[dict[str, Any]] | str:
    """Check source without saving it. uri is where it belongs.

    Returns errors (E) and warnings (W) with line and offset.
    """
    object_uri, source_uri = split_uri(uri)
    messages = await run(lambda c: c.syntax_check(object_uri, source_uri, source, version))
    return messages or "No errors or warnings."


@mcp.tool(annotations=READ)
async def run_unit_tests(
    uri: str,
    max_risk_level: Literal["harmless", "dangerous", "critical"] = "harmless",
    max_duration: Literal["short", "medium", "long"] = "medium",
) -> list[dict[str, Any]] | str:
    """Run the ABAP Unit tests of an object or package. Returns failed tests and warnings."""
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
    object_uri = split_uri(uri)[0]
    return await run(lambda c: c.run_unit_test(object_uri, flags)) or "No failed tests."


@mcp.tool(annotations=READ)
async def run_atc(
    object_uris: Union[str, list[str]],
    check_variant: Optional[str] = None,
    max_findings: int = 100,
) -> dict[str, Any]:
    """Run the ABAP Test Cockpit on objects or packages.

    Finding priority: 1 error, 2 warning, 3 information. atc_documentation explains a finding.
    """
    return await run(lambda c: c.run_atc(object_uris, check_variant, max_findings))


@mcp.tool(annotations=READ)
async def list_check_variants(pattern: str = "*", max_results: int = 100) -> list[dict[str, Any]]:
    """ATC check variants matching a name pattern."""
    return await run(lambda c: c.list_check_variants(pattern, max_results))


@mcp.tool(annotations=READ)
async def atc_documentation(documentation_uri: str) -> str:
    """Explanation of an ATC finding."""
    return await run(lambda c: c.atc_documentation(documentation_uri))


@mcp.tool(annotations=READ)
async def list_atc_checks(
    category: Optional[str] = None, search: Optional[str] = None
) -> list[dict[str, Any]] | str:
    """ATC checks a check variant can contain, with their category (e.g. CI_PERFORMANCE).

    category and search (part of the name or description) narrow the list of about 150 checks.
    """
    checks = await run(lambda c: c.list_atc_checks())
    if category:
        checks = [check for check in checks if check["category"].upper() == category.upper()]
    if search:
        checks = [
            check
            for check in checks
            if search.lower() in check["name"].lower() or search.lower() in check["description"].lower()
        ]
    return [
        {"name": check["name"], "description": check["description"], "category": check["category"]}
        for check in checks
    ] or "No checks found."


@mcp.tool(annotations=READ)
async def get_atc_check(check: str) -> dict[str, Any]:
    """An ATC check's description, category and parameters with their description, kind
    (value, list or ranges) and default.
    """
    return await run(lambda c: c.get_atc_check(check))


@mcp.tool(annotations=READ)
async def get_check_variant(name: str) -> dict[str, Any]:
    """An ATC check variant of the new kind (CHKV) with its checks and their parameter values.
    Old Code Inspector variants such as DEFAULT can only be run, not read.
    """
    return await run(lambda c: c.get_check_variant(name))


@mcp.tool(annotations=WRITE)
async def save_check_variant(
    name: str,
    package: str,
    description: str,
    checks: list[AtcCheckSetting],
    transport: Optional[str] = None,
) -> str:
    """Create an ATC check variant, or overwrite one (all its checks are replaced), and activate it.
    run_atc runs it. A check that refuses its parameters makes the activation fail.
    """
    await run(lambda c: c.save_check_variant(name, package, description, plain(checks), transport))
    return f"Saved and activated check variant {name.upper()} with {len(checks)} checks"


@mcp.tool(annotations=DESTRUCTIVE)
async def delete_check_variant(name: str, transport: Optional[str] = None) -> str:
    """Delete an ATC check variant."""
    await run(lambda c: c.delete_check_variant(name, transport))
    return f"Deleted check variant {name.upper()}"
