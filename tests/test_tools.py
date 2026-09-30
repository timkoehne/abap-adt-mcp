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


async def call(tool, /, **arguments):
    async with Client(mcp) as session:
        return await session.call_tool(tool, arguments)


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
    await call("delete_object", object_uris=REPORT)
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


async def test_activate_several_objects_together(client):
    root = "/sap/bc/adt/ddic/ddl/sources/zi_root"
    child = "/sap/bc/adt/ddic/ddl/sources/zi_child/source/main"
    result = await call("activate", object_uris=[root, child])
    assert not result.is_error
    client.activate_objects.assert_called_once_with(
        [("ZI_ROOT", root), ("ZI_CHILD", "/sap/bc/adt/ddic/ddl/sources/zi_child")]
    )


async def test_delete_several_objects_together(client):
    uris = ["/sap/bc/adt/ddic/ddl/sources/zi_root", "/sap/bc/adt/ddic/ddl/sources/zi_child"]
    result = await call("delete_object", object_uris=uris, transport="K900001")
    assert not result.is_error
    client.delete_objects.assert_called_once_with(uris, "K900001")
    client.lock.assert_not_called()


async def test_domain_fixed_values_leave_out_unset_fields(client):
    await call(
        "create_domain",
        name="zstatus",
        package="$TMP",
        description="Status",
        data_type="CHAR",
        length=1,
        fixed_values=[{"low": "N", "text": "New"}, {"low": "1", "high": "9"}],
    )
    kwargs = client.create_domain.call_args.kwargs
    assert kwargs["fixed_values"] == [{"low": "N", "text": "New"}, {"low": "1", "high": "9", "text": ""}]


async def test_badi_filters_keep_their_nesting(client):
    implementation = {
        "name": "ZIMPL",
        "badi": "ZBADI",
        "implementing_class": "ZCL_IMPL",
        "filters": [[{"filter": "PLANT", "value": "1000"}], [{"filter": "PLANT", "low": "2000", "high": "2999"}]],
    }
    result = await call(
        "create_enhancement_implementation",
        name="zenho",
        package="$TMP",
        description="Impl",
        spot="ZSPOT",
        implementations=[implementation],
    )
    assert not result.is_error
    passed = client.create_enhancement_implementation.call_args.args[4]
    assert passed == [implementation]


async def test_invalid_arguments_reach_the_model(client):
    client.create_data_element.side_effect = ValueError("pass exactly one of domain, data_type and reference_to")
    result = await call("create_data_element", name="zde", package="$TMP", description="x")
    assert result.is_error
    assert "exactly one of domain" in text(result)


async def test_publish_returns_service_urls(client):
    client.publish_service_binding.return_value = ["/sap/opu/odata4/sap/zui_travel/srvd/sap/ztravel/0001/"]
    result = await call("publish_service_binding", name="ZUI_TRAVEL")
    assert "/sap/opu/odata4/sap/zui_travel/" in text(result)
