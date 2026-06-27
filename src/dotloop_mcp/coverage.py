"""Static and generated Dotloop MCP API coverage resources."""

from __future__ import annotations

import inspect
from dataclasses import dataclass

from dotloop import DotloopClient
from dotloop.auth import AuthClient

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
| Contacts | list, get, create, update, delete | Deferred | PII/write surface deferred | Not run |
| Folders | list, get, create, update | List/get exposed | Create/update deferred | Not run |
| Documents | list, get, upload, download | List/get/download exposed | Upload deferred | Not run |
| Participants | list, get, add, update, remove | List/get exposed | Writes deferred | Not run |
| Tasks | task reads and summary helpers | Reads exposed | None in v1 | Not run |
| Activity | reads, summary, type/user filters | Reads exposed | None in v1 | Not run |
| Templates | list/get/filter helpers | Reads exposed | None in v1 | Not run |
| Webhooks | subscription and event management | Deferred | Hosted/callback deferred | Not run |
| OAuth | authorization/exchange/refresh/revoke/validate | Deferred | Credential changes | Not run |

Live checks are disabled by default and require explicit authorization.
"""

_GENERIC_HTTP_METHODS = {"get", "post", "patch", "delete"}
_CLIENT_DOMAINS = (
    "account",
    "profile",
    "loop",
    "loop_detail",
    "loop_it",
    "contact",
    "folder",
    "document",
    "participant",
    "task",
    "activity",
    "template",
    "webhook",
)
_DOMAIN_LABELS = {
    "account": "Account",
    "profile": "Profiles",
    "loop": "Loops",
    "loop_detail": "Loop details",
    "loop_it": "Loop-it",
    "contact": "Contacts",
    "folder": "Folders",
    "document": "Documents",
    "participant": "Participants",
    "task": "Tasks",
    "activity": "Activity",
    "template": "Templates",
    "webhook": "Webhooks",
    "auth": "OAuth helper",
}


@dataclass(frozen=True)
class MethodCoverage:
    """Coverage status for a named Dotloop library method."""

    status: str
    exposure: str
    notes: str


_EXPOSED_METHODS: dict[str, MethodCoverage] = {
    "account.get_account": MethodCoverage(
        "Exposed",
        "`dotloop_get_account`",
        "Read-only account identity smoke target.",
    ),
    "profile.list_profiles": MethodCoverage("Exposed", "`dotloop_list_profiles`", "Read-only."),
    "profile.get_profile": MethodCoverage("Exposed", "`dotloop_get_profile`", "Read-only."),
    "loop.list_loops": MethodCoverage("Exposed", "`dotloop_list_loops`", "Read-only."),
    "loop.get_loop": MethodCoverage("Exposed", "`dotloop_get_loop`", "Read-only."),
    "loop_detail.get_loop_details": MethodCoverage(
        "Exposed",
        "`dotloop_get_loop_details`",
        "Read-only.",
    ),
    "folder.list_folders": MethodCoverage("Exposed", "`dotloop_list_folders`", "Read-only."),
    "folder.get_folder": MethodCoverage("Exposed", "`dotloop_get_folder`", "Read-only."),
    "document.list_documents": MethodCoverage(
        "Exposed",
        "`dotloop_list_documents`",
        "Read-only with optional folder scope.",
    ),
    "document.get_document": MethodCoverage(
        "Exposed",
        "`dotloop_get_document`",
        "Read-only with optional folder scope.",
    ),
    "document.download_document": MethodCoverage(
        "Exposed",
        "`dotloop_download_document`",
        "Size-limited base64 response.",
    ),
    "participant.list_participants": MethodCoverage(
        "Exposed",
        "`dotloop_list_participants`",
        "Read-only.",
    ),
    "participant.get_participant": MethodCoverage(
        "Exposed",
        "`dotloop_get_participant`",
        "Read-only.",
    ),
    "task.list_task_lists": MethodCoverage("Exposed", "`dotloop_list_task_lists`", "Read-only."),
    "task.get_task_list": MethodCoverage("Exposed", "`dotloop_get_task_list`", "Read-only."),
    "task.list_tasks": MethodCoverage("Exposed", "`dotloop_list_tasks`", "Read-only."),
    "task.get_task": MethodCoverage("Exposed", "`dotloop_get_task`", "Read-only."),
    "task.get_task_summary": MethodCoverage(
        "Exposed",
        "`dotloop_get_task_summary`",
        "Read-only helper.",
    ),
    "task.get_all_tasks_in_loop": MethodCoverage(
        "Exposed",
        "`dotloop_get_all_tasks_in_loop`",
        "Read-only helper.",
    ),
    "task.get_pending_tasks": MethodCoverage(
        "Exposed",
        "`dotloop_get_pending_tasks`",
        "Read-only helper.",
    ),
    "task.get_completed_tasks": MethodCoverage(
        "Exposed",
        "`dotloop_get_completed_tasks`",
        "Read-only helper.",
    ),
    "activity.list_loop_activity": MethodCoverage(
        "Exposed",
        "`dotloop_list_loop_activity`",
        "Read-only.",
    ),
    "activity.get_recent_activity": MethodCoverage(
        "Exposed",
        "`dotloop_get_recent_activity`",
        "Read-only helper.",
    ),
    "activity.get_activity_summary": MethodCoverage(
        "Exposed",
        "`dotloop_get_activity_summary`",
        "Read-only helper.",
    ),
    "activity.get_activity_by_type": MethodCoverage(
        "Exposed",
        "`dotloop_get_activity_by_type`",
        "Read-only filter helper.",
    ),
    "activity.get_activity_by_user": MethodCoverage(
        "Exposed",
        "`dotloop_get_activity_by_user`",
        "Read-only filter helper.",
    ),
    "template.list_loop_templates": MethodCoverage(
        "Exposed",
        "`dotloop_list_loop_templates`",
        "Read-only.",
    ),
    "template.get_loop_template": MethodCoverage(
        "Exposed",
        "`dotloop_get_loop_template`",
        "Read-only.",
    ),
    "template.find_template_by_name": MethodCoverage(
        "Exposed",
        "`dotloop_find_template_by_name`",
        "Read-only helper.",
    ),
    "template.get_template_summary": MethodCoverage(
        "Exposed",
        "`dotloop_get_template_summary`",
        "Read-only helper.",
    ),
    "template.get_templates_by_type": MethodCoverage(
        "Exposed",
        "`dotloop_get_templates_by_type`",
        "Read-only filter helper.",
    ),
    "template.get_default_templates": MethodCoverage(
        "Exposed",
        "`dotloop_get_default_templates`",
        "Read-only filter helper.",
    ),
    "template.get_custom_templates": MethodCoverage(
        "Exposed",
        "`dotloop_get_custom_templates`",
        "Read-only filter helper.",
    ),
}

_COVERED_METHODS: dict[str, MethodCoverage] = {
    "document.list_documents_in_folder": MethodCoverage(
        "Covered",
        "`dotloop_list_documents`",
        "Use `folder_id`.",
    ),
    "document.get_document_in_folder": MethodCoverage(
        "Covered",
        "`dotloop_get_document`",
        "Use `folder_id`.",
    ),
    "document.download_document_in_folder": MethodCoverage(
        "Covered",
        "`dotloop_download_document`",
        "Use `folder_id`.",
    ),
}

_DEFERRED_READ_METHODS: dict[str, MethodCoverage] = {
    "contact.list_contacts": MethodCoverage(
        "Deferred read",
        "None",
        "PII surface; add only with product need.",
    ),
    "contact.get_contact": MethodCoverage(
        "Deferred read",
        "None",
        "PII surface; add only with product need.",
    ),
    "document.resolve_owner_profile_id": MethodCoverage(
        "Deferred read",
        "None",
        "Internal helper; not a user-facing tool.",
    ),
    "webhook.list_subscriptions": MethodCoverage(
        "Deferred read",
        "None",
        "Hosted/callback ownership needed first.",
    ),
    "webhook.get_subscription": MethodCoverage(
        "Deferred read",
        "None",
        "Hosted/callback ownership needed first.",
    ),
    "webhook.get_subscription_summary": MethodCoverage(
        "Deferred read",
        "None",
        "Hosted/callback ownership needed first.",
    ),
    "webhook.get_all_subscriptions_summary": MethodCoverage(
        "Deferred read",
        "None",
        "Hosted/callback ownership needed first.",
    ),
    "webhook.list_events": MethodCoverage(
        "Deferred read",
        "None",
        "Hosted/callback ownership needed first.",
    ),
    "webhook.get_event": MethodCoverage(
        "Deferred read",
        "None",
        "Hosted/callback ownership needed first.",
    ),
    "webhook.get_failed_events": MethodCoverage(
        "Deferred read",
        "None",
        "Hosted/callback ownership needed first.",
    ),
    "webhook.validate_event_types": MethodCoverage(
        "Deferred read",
        "None",
        "Local validation helper; not a user-facing V1 tool.",
    ),
}

_DEFERRED_CREDENTIAL_METHODS: dict[str, MethodCoverage] = {
    "auth.get_authorization_url": MethodCoverage(
        "Deferred credential",
        "None",
        "Operator workflow, not V1 tool.",
    ),
    "auth.get_oauth_flow_helper": MethodCoverage(
        "Deferred credential",
        "None",
        "Operator workflow, not V1 tool.",
    ),
    "auth.exchange_code_for_token": MethodCoverage(
        "Deferred credential",
        "None",
        "Credential state change.",
    ),
    "auth.refresh_access_token": MethodCoverage(
        "Deferred credential",
        "None",
        "Credential state change.",
    ),
    "auth.revoke_token": MethodCoverage(
        "Deferred credential",
        "None",
        "Credential state change.",
    ),
    "auth.validate_token": MethodCoverage(
        "Deferred credential",
        "None",
        "Credential inspection; needs storage policy.",
    ),
}

_METHOD_COVERAGE_BY_KEY = {
    **_EXPOSED_METHODS,
    **_COVERED_METHODS,
    **_DEFERRED_READ_METHODS,
    **_DEFERRED_CREDENTIAL_METHODS,
}
_WRITE_PREFIXES = (
    "create_",
    "update_",
    "delete_",
    "remove_",
    "add_",
    "upload_",
    "activate_",
    "deactivate_",
    "ensure_",
)
_WRITE_METHOD_KEYS = {
    "loop_it.create_loop",
    "document.download_document_to_file",
}


def _public_domain_methods(domain_client: object) -> list[str]:
    methods: list[str] = []
    for method_name, _member in inspect.getmembers(domain_client, predicate=callable):
        if method_name.startswith("_") or method_name in _GENERIC_HTTP_METHODS:
            continue
        methods.append(method_name)
    return sorted(methods)


def _method_keys_for_installed_package() -> list[str]:
    client = DotloopClient(api_key="coverage-validation")
    method_keys: list[str] = []

    for domain_name in _CLIENT_DOMAINS:
        domain_client = getattr(client, domain_name)
        method_keys.extend(
            f"{domain_name}.{method_name}" for method_name in _public_domain_methods(domain_client)
        )

    auth = AuthClient(
        api_key="coverage-validation",
        client_id="coverage-validation",
        client_secret="coverage-validation",
        redirect_uri="http://localhost",
    )
    method_keys.extend(f"auth.{method_name}" for method_name in _public_domain_methods(auth))
    return sorted(set(method_keys))


def classify_method(method_key: str) -> MethodCoverage:
    """Classify one installed Dotloop library method."""
    explicit = _METHOD_COVERAGE_BY_KEY.get(method_key)
    if explicit is not None:
        return explicit

    method_name = method_key.split(".", maxsplit=1)[1]
    if method_key in _WRITE_METHOD_KEYS or method_name.startswith(_WRITE_PREFIXES):
        return MethodCoverage("Deferred write", "None", "Requires a gated mutation phase.")
    return MethodCoverage("Unclassified", "None", "Update Dotloop MCP coverage classification.")


def unclassified_method_keys() -> list[str]:
    """Return installed package methods with no coverage classification."""
    return [
        method_key
        for method_key in _method_keys_for_installed_package()
        if classify_method(method_key).status == "Unclassified"
    ]


def build_method_coverage_markdown() -> str:
    """Build method-level coverage markdown from the installed Dotloop package."""
    method_keys = _method_keys_for_installed_package()
    lines = [
        "# Dotloop Library Method Coverage",
        "",
        "This method-level map is grounded in local inspection of `dotloop==1.3.2`.",
        "Generic inherited HTTP helpers such as `get`, `post`, `patch`, and `delete`",
        "are excluded because MCP tools should wrap named domain methods, not arbitrary",
        "endpoint calls.",
        "",
        "| Domain | Library method | MCP status | MCP exposure | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for method_key in method_keys:
        domain_name, method_name = method_key.split(".", maxsplit=1)
        coverage = classify_method(method_key)
        lines.append(
            "| "
            f"{_DOMAIN_LABELS[domain_name]} | "
            f"`{domain_name}.{method_name}` | "
            f"{coverage.status} | "
            f"{coverage.exposure} | "
            f"{coverage.notes} |"
        )
    lines.append("")
    return "\n".join(lines)


METHOD_COVERAGE_MARKDOWN = build_method_coverage_markdown()
