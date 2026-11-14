"""ABAP Cloud: language versions of objects and release states of APIs."""

from typing import Any, Literal, Optional

from abap_adt_py.exceptions import NotFoundError

from ..app import mcp, run, split_uri
from ._annotations import READ, WRITE

LanguageVersions = Literal["standard", "cloudDevelopment", "keyUser"]


@mcp.tool(annotations=READ)
async def get_language_version(uri: str) -> dict[str, Any]:
    """ABAP language version of an object (standard, cloudDevelopment = ABAP for Cloud Development, keyUser)
    and the versions it may have. version is "" for objects without one (message classes, includes,
    function modules: they have their function group's).
    """
    return await run(lambda c: c.get_language_version(split_uri(uri)[0]))


def _matches(hit_type: str, object_type: str) -> bool:
    wanted = {"FUNC": "FUGR/FF", "FM": "FUGR/FF"}.get(object_type.upper(), object_type.upper())
    return hit_type == wanted or hit_type.split("/")[0] == wanted


@mcp.tool(annotations=READ)
async def get_api_release_state(object_type: str, name: str) -> dict[str, Any]:
    """Release state of an SAP API: whether it can be used in ABAP for Cloud Development, its state under
    each release contract (C1 = cloud development and key user apps) and the successors SAP names for it.

    object_type: CLAS, INTF, TABL, DDLS (CDS view), FUNC (function module), DTEL, DOMA, SUSO, ...
    state is e.g. RELEASED, DEPRECATED, NOT_RELEASED, NOT_TO_BE_RELEASED.
    """

    def read(c) -> dict[str, Any]:
        hits = [
            hit
            for hit in c.search_object(name, 50)
            if hit.get("name", "").upper() == name.upper() and _matches(hit.get("type", ""), object_type)
        ]
        if not hits:
            raise NotFoundError(f"No object {name.upper()} of type {object_type.upper()} found")
        state = c.get_api_release_state(hits[0]["uri"])
        result: dict[str, Any] = {
            "name": state["name"],
            "type": state["type"],
            "uri": state["uri"],
            "state": state["state"],
            "cloud_development": state["cloud_development"],
            "key_user": state["key_user"],
            "successors": [{"name": s["name"], "type": s["type"]} for s in state["successors"]],
            "contracts": [
                {"contract": contract["contract"], "state": contract["state"]}
                for contract in state["contracts"]
            ],
        }
        concepts = [contract["successor_concept"] for contract in state["contracts"] if contract["successor_concept"]]
        if concepts:
            result["successor_concepts"] = concepts
        return result

    return await run(read)


@mcp.tool(annotations=WRITE)
async def set_language_version(
    uri: str, version: LanguageVersions, transport: Optional[str] = None
) -> str:
    """Change an object's ABAP language version and activate it.

    Works for classes, interfaces, function groups, tables, structures, CDS views, data elements, domains and
    more; not for reports. If the code uses what the version forbids (e.g. APIs not released for cloud
    development), the activation errors are returned and the active version stays as it was.
    """
    object_uri = split_uri(uri)[0]
    await run(lambda c: c.set_language_version(object_uri, version, transport))
    return f"{object_uri} is active in {version}"
