"""Tool schemas without what pydantic generates and no client needs: every model reads them on every call."""

from typing import Any

from ..app import mcp


def compact(schema: Any) -> Any:
    """The schema without generated titles; an optional value shows as its own type, not as "X or null"."""
    if isinstance(schema, list):
        return [compact(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    out = {}
    for key, value in schema.items():
        if key == "properties":
            out[key] = {name: compact(prop) for name, prop in value.items()}
        elif key != "title":
            out[key] = compact(value)
    options = out.get("anyOf")
    if options and {"type": "null"} in options:
        rest = [option for option in options if option != {"type": "null"}]
        del out["anyOf"]
        out.pop("default", None)
        if len(rest) == 1:
            out.update(rest[0])
        else:
            out["anyOf"] = rest
    return out


def compact_tool_schemas() -> None:
    for tool in mcp._tool_manager.list_tools():
        tool.parameters = compact(tool.parameters)
