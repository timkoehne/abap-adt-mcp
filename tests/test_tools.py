from unittest.mock import MagicMock

import pytest
from abap_adt_py.exceptions import ActivationError, ObjectLockedError
from mcp import Client

from abap_adt_mcp import app
from abap_adt_mcp.server import mcp
from abap_adt_mcp.tools._schema import compact

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
    include = "/sap/bc/adt/programs/includes/z_test_f01"
    assert app.split_uri(include) == (include, f"{include}/source/main")
    assert app.split_uri(f"{include}/source/main")[0] == include
    assert app.object_name(include) == "Z_TEST_F01"
    top = "/sap/bc/adt/functions/groups/z_grp/includes/lz_grptop"
    assert app.split_uri(top) == (top, f"{top}/source/main")
    assert app.split_uri(f"{top}/source/main")[0] == top
    assert app.object_name(top) == "LZ_GRPTOP"


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
    await call("run_unit_tests", uri=REPORT, max_risk_level="dangerous", max_duration="long")
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


async def test_authorization_object_defaults_to_cross_application_class(client):
    result = await call(
        "create_authorization_object",
        name="zao_test",
        package="$TMP",
        description="Test",
        fields=["ZAF_TEST", "ACTVT"],
        activities=["01", "03"],
    )
    assert not result.is_error
    client.create_authorization_object.assert_called_once_with(
        "zao_test", "$TMP", "Test", "AAAB", ["ZAF_TEST", "ACTVT"], ["01", "03"], None
    )
    assert "ZAO_TEST" in text(result)


async def test_authorization_field_update_passes_empty_check_table(client):
    await call("update_authorization_field", name="ZAF_TEST", check_table="")
    client.update_authorization_field.assert_called_once_with("ZAF_TEST", None, "", None)


def test_compact_schema():
    schema = {
        "title": "Args",
        "properties": {
            "title": {"title": "Title", "type": "string"},
            "transport": {"anyOf": [{"type": "string"}, {"type": "null"}], "default": None, "title": "Transport"},
            "uris": {"anyOf": [{"type": "string"}, {"items": {"type": "string"}, "type": "array"}], "title": "Uris"},
            "max": {"default": 20, "title": "Max", "type": "integer"},
        },
    }
    assert compact(schema) == {
        "properties": {
            "title": {"type": "string"},
            "transport": {"type": "string"},
            "uris": {"anyOf": [{"type": "string"}, {"items": {"type": "string"}, "type": "array"}]},
            "max": {"default": 20, "type": "integer"},
        },
    }


async def test_listed_schemas_are_compact_and_optional_values_still_accept_null(client):
    async with Client(mcp) as session:
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}
    write = tools["write_source"].input_schema
    assert "title" not in write and "title" not in write["properties"]["uri"]
    assert write["properties"]["transport"] == {"type": "string"}
    assert write["required"] == ["uri", "source"]
    result = await call("write_source", uri=REPORT, source="REPORT z_test.", transport=None)
    assert not result.is_error


@pytest.mark.parametrize(
    "tool, method, arguments, answer",
    [
        ("search_objects", "search_object", {"query": "ZNONE*"}, "No objects found."),
        ("package_contents", "package_contents", {"package": "$TMP"}, "The package is empty."),
        ("syntax_check", "syntax_check", {"uri": REPORT, "source": "REPORT z."}, "No errors or warnings."),
        ("run_unit_tests", "run_unit_test", {"uri": REPORT}, "No failed tests."),
        ("where_used", "where_used", {"uri": REPORT}, "Not used anywhere."),
        ("list_dumps", "list_dumps", {}, "No dumps found."),
    ],
)
async def test_an_empty_answer_says_so(client, tool, method, arguments, answer):
    getattr(client, method).return_value = []
    result = await call(tool, **arguments)
    assert not result.is_error
    assert text(result) == answer
    assert result.structured_content == {"result": answer}


async def test_a_list_answer_stays_a_list(client):
    client.search_object.return_value = [{"name": "Z_TEST", "uri": REPORT}]
    result = await call("search_objects", query="Z_TEST*")
    assert '"Z_TEST"' in text(result)
    assert result.structured_content == {"result": [{"name": "Z_TEST", "uri": REPORT}]}


async def test_a_name_instead_of_a_uri_gets_a_clear_error(client):
    result = await call("get_source", uri="ZCL_KAS_ORDER")
    assert result.is_error
    assert "ZCL_KAS_ORDER is not a uri" in text(result)
    assert "/sap/bc/adt/oo/classes/zcl_demo" in text(result)
    client.get_object_source.assert_not_called()


async def test_an_unexpected_error_keeps_its_reason(client):
    client.search_object.side_effect = KeyError("adtcore:name")
    result = await call("search_objects", query="Z*")
    assert result.is_error
    assert "KeyError" in text(result) and "adtcore:name" in text(result)


async def test_create_object_in_a_language_version(client):
    result = await call(
        "create_object", object_type="CLAS/OC", name="zcl_x", package="$TMP", description="x",
        language_version="cloudDevelopment",
    )
    assert not result.is_error
    client.create.assert_called_once_with("CLAS/OC", "zcl_x", "$TMP", "x", None, "cloudDevelopment")
    assert text(result) == "Created CLAS/OC ZCL_X in cloudDevelopment"


async def test_create_object_without_a_version_answers_as_before(client):
    result = await call("create_object", object_type="PROG/P", name="z_test", package="$TMP", description="x")
    client.create.assert_called_once_with("PROG/P", "z_test", "$TMP", "x", None, None)
    assert text(result) == "Created PROG/P Z_TEST"


async def test_language_version_takes_a_source_uri(client):
    client.get_language_version.return_value = {"name": "ZCL_X", "version": "standard"}
    await call("get_language_version", uri="/sap/bc/adt/oo/classes/zcl_x/source/main")
    client.get_language_version.assert_called_once_with("/sap/bc/adt/oo/classes/zcl_x")
    result = await call("set_language_version", uri="/sap/bc/adt/oo/classes/zcl_x", version="cloudDevelopment")
    client.set_language_version.assert_called_once_with("/sap/bc/adt/oo/classes/zcl_x", "cloudDevelopment", None)
    assert "cloudDevelopment" in text(result)


async def test_unknown_language_version_is_refused(client):
    result = await call("set_language_version", uri="/sap/bc/adt/oo/classes/zcl_x", version="5")
    assert result.is_error
    client.set_language_version.assert_not_called()


async def test_api_release_state_finds_the_object_by_type_and_name(client):
    client.search_object.return_value = [
        {"name": "WAERS", "type": "DOMA/DD", "uri": "/sap/bc/adt/ddic/domains/waers"},
        {"name": "WAERS", "type": "DTEL/DE", "uri": "/sap/bc/adt/ddic/dataelements/waers"},
    ]
    client.get_api_release_state.return_value = {
        "name": "WAERS", "type": "DTEL/DE", "uri": "/sap/bc/adt/ddic/dataelements/waers", "state": "RELEASED",
        "cloud_development": True, "key_user": True, "successors": [],
        "contracts": [{"contract": "C1", "state": "RELEASED", "successor_concept": "", "comment": ""}],
    }
    result = await call("get_api_release_state", object_type="DTEL", name="waers")
    assert not result.is_error
    client.get_api_release_state.assert_called_once_with("/sap/bc/adt/ddic/dataelements/waers")
    assert result.structured_content["contracts"] == [{"contract": "C1", "state": "RELEASED"}]


async def test_api_release_state_of_a_function_module(client):
    uri = "/sap/bc/adt/functions/groups/snr3/fmodules/number_get_next"
    client.search_object.return_value = [{"name": "NUMBER_GET_NEXT", "type": "FUGR/FF", "uri": uri}]
    client.get_api_release_state.return_value = {
        "name": "NUMBER_GET_NEXT", "type": "FUGR/FF", "uri": uri, "state": "NOT_TO_BE_RELEASED",
        "cloud_development": False, "key_user": False,
        "successors": [{"name": "CL_NUMBERRANGE_RUNTIME", "type": "CLAS/OC", "uri": "/sap/bc/adt/oo/classes/cl_numberrange_runtime"}],
        "contracts": [],
    }
    result = await call("get_api_release_state", object_type="FUNC", name="NUMBER_GET_NEXT")
    assert result.structured_content["successors"] == [{"name": "CL_NUMBERRANGE_RUNTIME", "type": "CLAS/OC"}]


async def test_api_release_state_of_an_unknown_object(client):
    client.search_object.return_value = []
    result = await call("get_api_release_state", object_type="CLAS", name="CL_NONE")
    assert result.is_error
    assert text(result).endswith("No object CL_NONE of type CLAS found")
    client.get_api_release_state.assert_not_called()


async def test_list_atc_checks_filters(client):
    client.list_atc_checks.return_value = [
        {"name": "CI_SYSUBRC", "description": "Check of SY-SUBRC Handling", "category": "CI_ROBUSTNESS", "category_description": "Robustness"},
        {"name": "CI_DB_OPS_IN_LOOPS", "description": "Search DB Operations in loops", "category": "CI_PERFORMANCE", "category_description": "Performance"},
    ]
    result = await call("list_atc_checks", search="sy-subrc")
    assert result.structured_content == {
        "result": [{"name": "CI_SYSUBRC", "description": "Check of SY-SUBRC Handling", "category": "CI_ROBUSTNESS"}]
    }
    result = await call("list_atc_checks", category="ci_performance")
    assert [c["name"] for c in result.structured_content["result"]] == ["CI_DB_OPS_IN_LOOPS"]
    result = await call("list_atc_checks", category="NONE")
    assert text(result) == "No checks found."


async def test_save_check_variant_passes_the_checks_as_dicts(client):
    result = await call(
        "save_check_variant", name="zcv", package="$TMP", description="d",
        checks=[{"name": "CI_SYSUBRC", "parameters": {"ReadDB": True}}, {"name": "CI_NO_ORDER_BY"}],
    )
    assert not result.is_error
    client.save_check_variant.assert_called_once_with(
        "zcv", "$TMP", "d", [{"name": "CI_SYSUBRC", "parameters": {"ReadDB": True}}, {"name": "CI_NO_ORDER_BY"}], None
    )
    assert text(result) == "Saved and activated check variant ZCV with 2 checks"


async def test_delete_check_variant(client):
    result = await call("delete_check_variant", name="zcv")
    client.delete_check_variant.assert_called_once_with("zcv", None)
    assert text(result) == "Deleted check variant ZCV"


async def test_create_lock_object(client):
    result = await call(
        "create_lock_object", name="ezlock", package="$TMP", description="d", primary_table="ZHEAD",
        secondary_tables=[{"table": "ZITEM"}], parameters=["MANDT", {"name": "POS", "table": "ZITEM"}],
    )
    assert not result.is_error
    client.create_lock_object.assert_called_once_with(
        "ezlock", "$TMP", "d", "ZHEAD", "E", [{"table": "ZITEM"}], ["MANDT", {"name": "POS", "table": "ZITEM"}],
        False, None,
    )
    assert "ENQUEUE_EZLOCK" in text(result)


async def test_job_template_parameters(client):
    result = await call(
        "create_job_template", name="zjt", package="$TMP", description="d", catalog_entry="ZJC",
        parameters={"P_ID": "A1", "S_DATE": [{"sign": "I", "option": "BT", "low": "20250101", "high": "20251231"}]},
    )
    assert not result.is_error
    client.create_job_template.assert_called_once_with(
        "zjt", "$TMP", "d", "ZJC",
        {"P_ID": "A1", "S_DATE": [{"sign": "I", "option": "BT", "low": "20250101", "high": "20251231"}]}, None,
    )


async def test_job_catalog_entry_leaves_out_the_raw_source(client):
    client.get_job_catalog_entry.return_value = {
        "name": "ZJC", "description": "d", "class_name": "ZCL_JOB", "parameters": [{"name": "P_ID"}], "source": {"x": 1},
    }
    result = await call("get_job_catalog_entry", name="zjc")
    assert result.structured_content == {
        "name": "ZJC", "description": "d", "class_name": "ZCL_JOB", "parameters": [{"name": "P_ID"}]
    }


async def test_application_log_object(client):
    await call("create_application_log_object", name="zlog", package="$TMP", description="d", subobjects=[{"name": "RUN"}])
    client.create_application_log_object.assert_called_once_with("zlog", "$TMP", "d", [{"name": "RUN", "description": ""}], None)
