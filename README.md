# abap-adt-mcp

An [MCP](https://modelcontextprotocol.io) server that gives AI agents access to an SAP system through the
ABAP Development Tools (ADT) REST API. It is a thin layer over the
[abap-adt-py](https://github.com/timkoehne/abap-adt-py) library: search and browse the repository, read and write
source code, activate, run syntax checks, unit tests and ATC, run SQL queries and classes, read short dumps and
manage transport requests.

## Running

```bash
cp .env.example .env   # fill in the SAP connection and a token
uv run --env-file .env abap-adt-mcp
```

Without a checkout, run the PyPI release: `uvx --env-file .env abap-adt-mcp`.

The server speaks Streamable HTTP at `http://<ADT_MCP_HOST>:<ADT_MCP_PORT>/mcp` (default `http://127.0.0.1:2236/mcp`).
It logs in to SAP on the first tool call and keeps one session for all clients.

| Variable | Default | |
|---|---|---|
| `ABAP_ADT_HOST` | | SAP system, e.g. `http://localhost:50000` |
| `ABAP_ADT_USER`, `ABAP_ADT_PASSWORD` | | SAP login |
| `ABAP_ADT_CLIENT`, `ABAP_ADT_LANGUAGE` | `001`, `EN` | |
| `ADT_MCP_HOST`, `ADT_MCP_PORT` | `127.0.0.1`, `2236` | where the server listens |
| `ADT_MCP_TOKEN` | | required `Authorization: Bearer` token; mandatory on non-local addresses |

### Claude Code

```bash
claude mcp add --transport http abap-adt http://localhost:2236/mcp --header "Authorization: Bearer <token>"
```

## Tools

| Area | Tools |
|---|---|
| Repository | `search_objects`, `package_contents`, `object_package_path`, `object_structure` |
| Source | `get_source`, `write_source`, `activate`, `pretty_print` |
| Create / delete | `create_object`, `create_package`, `create_domain`, `create_table_type`, `create_service_binding`, `create_test_class_include`, `delete_object` |
| Quality | `syntax_check`, `run_unit_tests`, `run_atc`, `list_check_variants`, `atc_documentation` |
| Navigation | `find_definition`, `where_used`, `code_completion` |
| Runtime | `run_query`, `run_class`, `list_dumps`, `get_dump` |
| Transports | `transport_info`, `create_transport`, `list_transports`, `release_transport`, `delete_transport` |

Locking is handled inside the tools: `write_source` locks the object, writes, unlocks and activates, so agents
never deal with lock handles. SAP errors (activation errors with their positions, locked objects, ...) are
returned to the agent as tool errors.

## Development

```bash
uv sync
uv run pytest
```
