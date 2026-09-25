import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SapSettings:
    host: str
    user: str
    password: str
    client: str
    language: str


@dataclass(frozen=True)
class ServerSettings:
    host: str
    port: int
    # clients must send "Authorization: Bearer <token>", no check if empty
    token: str


def _required(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"environment variable {name} is not set")
    return value


def sap_settings() -> SapSettings:
    """SAP connection from the same ABAP_ADT_* variables the library's tests use."""
    return SapSettings(
        host=_required("ABAP_ADT_HOST"),
        user=_required("ABAP_ADT_USER"),
        password=_required("ABAP_ADT_PASSWORD"),
        client=os.environ.get("ABAP_ADT_CLIENT", "001"),
        language=os.environ.get("ABAP_ADT_LANGUAGE", "EN"),
    )


def server_settings() -> ServerSettings:
    return ServerSettings(
        host=os.environ.get("ADT_MCP_HOST", "127.0.0.1"),
        port=int(os.environ.get("ADT_MCP_PORT", "2236")),
        token=os.environ.get("ADT_MCP_TOKEN", ""),
    )
