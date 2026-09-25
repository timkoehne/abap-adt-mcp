from unittest.mock import MagicMock

import pytest
from abap_adt_py.exceptions import ActivationError, ObjectLockedError
from mcp import Client

from abap_adt_mcp import app
from abap_adt_mcp.server import mcp

REPORT = "/sap/bc/adt/programs/programs/z_test"


@pytest.fixture
def client(monkeypatch):
    fake = MagicMock()
    fake.lock.return_value = "HANDLE"
    monkeypatch.setattr(app, "_client", fake)
    return fake


async def call(name, **arguments):
    async with Client(mcp) as session:
        return await session.call_tool(name, arguments)


def text(result) -> str:
    return "".join(getattr(block, "text", "") for block in result.content)


def test_split_uri():
    assert app.split_uri(REPORT) == (REPORT, f"{REPORT}/source/main")
    assert app.split_uri(f"{REPORT}/source/main") == (REPORT, f"{REPORT}/source/main")
    cls = "/sap/bc/adt/oo/classes/zcl_x"
    assert app.split_uri(f"{cls}/includes/testclasses")[0] == cls
    assert app.object_name(cls) == "ZCL_X"


async def test_all_tools_listed():
    async with Client(mcp) as session:
        names = {tool.name for tool in (await session.list_tools()).tools}
    assert {"search_objects", "get_source", "write_source", "run_query", "delete_object"} <= names
    assert not names & {"lock", "unlock", "set_object_source"}


async def test_search_returns_structured_hits(client):
    client.search_object.return_value = [{"name": "Z_TEST", "uri": REPORT}]
    result = await call("search_objects", query="Z_TEST*")
    assert not result.is_error
    client.search_object.assert_called_once_with("Z_TEST*", 20)
    assert "Z_TEST" in text(result)


async def test_get_source_accepts_object_uri(client):
    client.get_object_source.return_value = "REPORT z_test."
    result = await call("get_source", uri=REPORT)
    client.get_object_source.assert_called_once_with(f"{REPORT}/source/main", "active")
    assert text(result) == "REPORT z_test."


async def test_write_source_locks_writes_unlocks_activates(client):
    result = await call("write_source", uri=REPORT, source="REPORT z_test.")
    assert not result.is_error
    client.lock.assert_called_once_with(REPORT)
    client.set_object_source.assert_called_once_with(
        f"{REPORT}/source/main", "REPORT z_test.", "HANDLE", None
    )
    client.unlock.assert_called_once_with(REPORT, "HANDLE")
    client.activate.assert_called_once_with("Z_TEST", REPORT)


async def test_write_source_unlocks_when_writing_fails(client):
    client.set_object_source.side_effect = ObjectLockedError(
        "403 - Failed to write: User X is currently editing Z_TEST", sap_message="User X is currently editing Z_TEST"
    )
    result = await call("write_source", uri=REPORT, source="x")
    assert result.is_error
    assert "currently editing" in text(result)
    client.unlock.assert_called_once_with(REPORT, "HANDLE")
    client.activate.assert_not_called()


async def test_failed_unlock_drops_session(client):
    client.unlock.side_effect = RuntimeError("connection lost")
    await call("delete_object", object_uri=REPORT)
    assert app._client is None


async def test_activation_errors_reach_the_model(client):
    client.activate.side_effect = ActivationError(
        "Activation of Z_TEST failed: syntax error",
        messages=[{"type": "E", "text": "Field FOO is unknown", "uri": f"{REPORT}#start=3,4"}],
    )
    result = await call("write_source", uri=REPORT, source="x")
    assert result.is_error
    assert "Field FOO is unknown" in text(result)
    assert "#start=3,4" in text(result)


async def test_unit_test_flags(client):
    client.run_unit_test.return_value = []
    await call("run_unit_tests", object_uri=REPORT, max_risk_level="dangerous", max_duration="long")
    flags = client.run_unit_test.call_args.args[1]
    assert (flags.harmless, flags.dangerous, flags.critical) == (True, True, False)
    assert (flags.short, flags.medium, flags.long) == (True, True, True)


async def test_connection_errors_reach_the_model(client):
    import requests

    client.run_query.side_effect = requests.ConnectionError("Name or service not known")
    result = await call("run_query", query="SELECT * FROM t000")
    assert result.is_error
    assert "Connection to the SAP system failed" in text(result)
    assert app._client is None
