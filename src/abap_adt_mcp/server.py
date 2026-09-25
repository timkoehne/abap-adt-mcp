import hmac

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from . import tools  # noqa: F401  registers the tools
from .app import mcp
from .config import sap_settings, server_settings

LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")


class BearerTokenMiddleware:
    """Rejects HTTP requests without "Authorization: Bearer <token>"."""

    def __init__(self, app: ASGIApp, token: str):
        self.app = app
        self.expected = f"Bearer {token}".encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            received = dict(scope["headers"]).get(b"authorization", b"")
            if not hmac.compare_digest(received, self.expected):
                await PlainTextResponse("Unauthorized", status_code=401)(scope, receive, send)
                return
        await self.app(scope, receive, send)


def build_app() -> ASGIApp:
    settings = server_settings()
    if not settings.token and settings.host not in LOCAL_HOSTS:
        raise RuntimeError("set ADT_MCP_TOKEN when listening on a non-local address")

    security = None
    if settings.host not in LOCAL_HOSTS:
        # DNS rebinding protection only knows localhost by default
        security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

    app: ASGIApp = mcp.streamable_http_app(host=settings.host, transport_security=security)
    if settings.token:
        app = BearerTokenMiddleware(app, settings.token)
    return app


def main() -> None:
    sap_settings()  # fail at startup, not on the first tool call, if the SAP login isn't configured
    settings = server_settings()
    uvicorn.run(build_app(), host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
