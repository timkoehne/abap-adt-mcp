"""Importing this package registers all tools on the MCPServer instance."""

from . import (  # noqa: F401
    authorization,
    create,
    ddic,
    enhancements,
    messages,
    navigation,
    quality,
    repository,
    runtime,
    services,
    source,
    transport,
)
from ._schema import compact_tool_schemas

compact_tool_schemas()
