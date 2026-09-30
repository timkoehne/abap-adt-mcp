from typing import Any, Optional

from ..app import mcp, run
from ._annotations import DESTRUCTIVE, READ, WRITE
from ._models import Message, plain


@mcp.tool(annotations=WRITE)
async def create_message_class(
    name: str,
    package: str,
    description: str,
    messages: Optional[list[Message]] = None,
    transport: Optional[str] = None,
) -> str:
    """Create a message class, optionally with messages, e.g. [{"number": "001", "text": "Bin &1 is blocked"}]."""
    await run(
        lambda c: c.create_message_class(name, package, description, plain(messages), transport)
    )
    return f"Created message class {name.upper()}"


@mcp.tool(annotations=READ)
async def get_message_class(name: str) -> dict[str, Any]:
    """A message class with its description, package and messages."""
    return await run(lambda c: c.get_message_class(name))


@mcp.tool(annotations=WRITE)
async def set_messages(
    message_class: str,
    messages: list[Message],
    delete_others: bool = False,
    transport: Optional[str] = None,
) -> str:
    """Add or change messages of a message class.

    Messages not in the list are kept, unless delete_others=True.
    """
    await run(
        lambda c: c.set_messages(message_class, plain(messages), transport, delete_others)
    )
    return f"Saved {len(messages)} messages in {message_class.upper()}"


@mcp.tool(annotations=DESTRUCTIVE)
async def delete_messages(
    message_class: str, numbers: list[str], transport: Optional[str] = None
) -> str:
    """Delete messages from a message class by their numbers."""
    await run(lambda c: c.delete_messages(message_class, numbers, transport))
    return f"Deleted messages {', '.join(numbers)} from {message_class.upper()}"
