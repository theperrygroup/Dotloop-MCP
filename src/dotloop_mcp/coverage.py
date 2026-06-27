"""Static Dotloop MCP API coverage resource."""

from __future__ import annotations

COVERAGE_RESOURCE_URI = "dotloop://api-coverage-matrix"
METHOD_COVERAGE_RESOURCE_URI = "dotloop://library-method-coverage"

API_COVERAGE_MARKDOWN = """# Dotloop MCP API Coverage Matrix

This matrix is grounded in `dotloop==1.3.2`.

| Domain | Library operations | V1 MCP status | Mutation risk | Live status |
| --- | --- | --- | --- | --- |
| Account | get account | Exposed read | None | Not run |
| Profiles | list, get, create, update | List/get exposed | Create/update deferred | Not run |
| Loops | list, get, create, update | List/get exposed | Create/update deferred | Not run |
| Loop details | get and update detail groups | Get exposed | Updates deferred | Not run |
| Loop-it | simplified loop create | Deferred | Creates loop | Not run |
| Contacts | list, get, create, update, delete | Deferred | Writes deferred | Not run |
| Folders | list, get, create, update | List/get exposed | Create/update deferred | Not run |
| Documents | list, get, upload, download | List/get/download exposed | Upload deferred | Not run |
| Participants | list, get, add, update, remove | List/get exposed | Writes deferred | Not run |
| Tasks | task list/task reads and summary helpers | Reads exposed | None in v1 | Not run |
| Activity | loop activity reads and summary helpers | Reads exposed | None in v1 | Not run |
| Templates | list/get/filter/summary helpers | Reads exposed | None in v1 | Not run |
| Webhooks | subscription and event management | Deferred | Mutations deferred | Not run |
| OAuth | authorization/exchange/refresh/revoke/validate | Deferred | Credential changes | Not run |

Live checks are disabled by default and require explicit authorization.
"""

METHOD_COVERAGE_MARKDOWN = """# Dotloop Library Method Coverage

This fallback resource points to `docs/api/dotloop-library-method-coverage.md`
for method-level coverage grounded in `dotloop==1.3.2`.
"""
