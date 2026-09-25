"""The MCPServer instance and the shared AdtClient every tool goes through."""

import threading
from typing import Callable, Optional, Tuple, TypeVar
from urllib.parse import unquote

import anyio.to_thread
import requests
from abap_adt_py.adt_client import AdtClient
from abap_adt_py.exceptions import ActivationError, AdtError
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .config import sap_settings

T = TypeVar("T")

INSTRUCTIONS = """\
Tools for an SAP system via the ABAP Development Tools (ADT) REST API.

Objects are addressed by ADT URIs, e.g.
  /sap/bc/adt/programs/programs/z_report      report
  /sap/bc/adt/oo/classes/zcl_demo             class
  /sap/bc/adt/oo/interfaces/zif_demo          interface
  /sap/bc/adt/ddic/ddl/sources/z_cds_view     CDS view
  /sap/bc/adt/packages/z_demo                 package
search_objects returns the URI of every hit. Source code lives below the object at
<object uri>/source/main (class includes: <class uri>/includes/testclasses, ...);
tools taking an object URI also accept a source URI and vice versa.
Lines are 1-based, columns 0-based. Local objects go to package $TMP and need no
transport; objects in transportable packages need a transport request number.
"""

mcp = MCPServer("abap-adt", instructions=INSTRUCTIONS)

_client: Optional[AdtClient] = None
# AdtClient is synchronous and keeps session state (CSRF token, locks), so only
# one tool uses it at a time
_client_lock = threading.Lock()


def _get_client() -> AdtClient:
    global _client
    if _client is None:
        settings = sap_settings()
        client = AdtClient(
            sap_host=settings.host,
            username=settings.user,
            password=settings.password,
            client=settings.client,
            language=settings.language,
        )
        client.login()
        _client = client
    return _client


def reset_client() -> None:
    """Drop the session, the next tool call logs in again."""
    global _client
    _client = None


def error_text(error: AdtError) -> str:
    text = str(error)
    if isinstance(error, ActivationError) and error.messages:
        lines = [
            f"[{m.get('type', '')}] {m.get('text', '')} ({m.get('uri', '')})"
            for m in error.messages
        ]
        text += "\n" + "\n".join(lines)
    return text


async def run(fn: Callable[[AdtClient], T]) -> T:
    """Run fn with the shared client in a worker thread, SAP errors become tool errors."""

    def locked() -> T:
        with _client_lock:
            return fn(_get_client())

    try:
        return await anyio.to_thread.run_sync(locked)
    except AdtError as error:
        raise ToolError(error_text(error)) from error
    except requests.RequestException as error:
        reset_client()
        raise ToolError(f"Connection to the SAP system failed: {error}") from error


def split_uri(uri: str) -> Tuple[str, str]:
    """(object uri, source uri) from either of them."""
    uri = uri.rstrip("/")
    for marker in ("/source/", "/includes/"):
        if marker in uri:
            return uri.split(marker, 1)[0], uri
    return uri, f"{uri}/source/main"


def object_name(object_uri: str) -> str:
    return unquote(object_uri.rstrip("/").rsplit("/", 1)[-1]).upper()


def with_lock(client: AdtClient, object_uri: str, fn: Callable[[str], T]) -> T:
    """Lock the object, call fn with the lock handle and always unlock again."""
    handle = client.lock(object_uri)
    try:
        return fn(handle)
    finally:
        try:
            client.unlock(object_uri, handle)
        except Exception:
            # the lock belongs to the session, dropping the session releases it
            reset_client()
