"""Grouped FastMCP registration for the Dotloop server."""

from __future__ import annotations

from pathlib import Path

from dotloop_mcp.coverage import (
    API_COVERAGE_MARKDOWN,
    COVERAGE_RESOURCE_URI,
    METHOD_COVERAGE_MARKDOWN,
    METHOD_COVERAGE_RESOURCE_URI,
)
from dotloop_mcp.mcp_tools import (
    ActivityByTypeToolInput,
    ActivityByUserToolInput,
    DotloopToolAdapter,
    FindTemplateToolInput,
    GetFolderToolInput,
    ListActivityToolInput,
    ListDocumentsToolInput,
    ListFoldersToolInput,
    ListLoopsToolInput,
    RecentActivityToolInput,
    TemplateTypeToolInput,
    validate_request,
)
from dotloop_mcp.models.common import (
    DocumentRequest,
    DownloadDocumentRequest,
    JsonObject,
    ParticipantRequest,
    ProfileIdRequest,
    ProfileLoopRequest,
    TaskListRequest,
    TaskRequest,
    TemplateRequest,
)
from mcp.server.fastmcp import FastMCP


def register_server_surface(
    mcp: FastMCP,
    adapter: DotloopToolAdapter,
    *,
    project_root: Path,
) -> None:
    """Register Dotloop MCP tools and resources."""
    _register_account_tools(mcp, adapter)
    _register_profile_tools(mcp, adapter)
    _register_loop_tools(mcp, adapter)
    _register_folder_tools(mcp, adapter)
    _register_document_tools(mcp, adapter)
    _register_participant_tools(mcp, adapter)
    _register_task_tools(mcp, adapter)
    _register_activity_tools(mcp, adapter)
    _register_template_tools(mcp, adapter)
    _register_resources(mcp, project_root=project_root)


def _register_account_tools(mcp: FastMCP, adapter: DotloopToolAdapter) -> None:
    @mcp.tool(name="dotloop_get_account", description="Get the current Dotloop account.")
    async def dotloop_get_account() -> JsonObject:
        return await adapter.get_account()


def _register_profile_tools(mcp: FastMCP, adapter: DotloopToolAdapter) -> None:
    @mcp.tool(name="dotloop_list_profiles", description="List Dotloop profiles.")
    async def dotloop_list_profiles() -> JsonObject:
        return await adapter.list_profiles()

    @mcp.tool(name="dotloop_get_profile", description="Get one Dotloop profile by ID.")
    async def dotloop_get_profile(profile_id: int) -> JsonObject:
        request = validate_request(ProfileIdRequest, locals())
        return await adapter.get_profile(request)


def _register_loop_tools(mcp: FastMCP, adapter: DotloopToolAdapter) -> None:
    @mcp.tool(name="dotloop_list_loops", description="List loops for a Dotloop profile.")
    async def dotloop_list_loops(
        profile_id: int,
        batch_size: int = 100,
        batch_number: int = 1,
        sort: str | None = None,
        include_details: bool = False,
    ) -> JsonObject:
        request = validate_request(ListLoopsToolInput, locals())
        return await adapter.list_loops(request)

    @mcp.tool(name="dotloop_get_loop", description="Get one Dotloop loop.")
    async def dotloop_get_loop(profile_id: int, loop_id: int) -> JsonObject:
        request = validate_request(ProfileLoopRequest, locals())
        return await adapter.get_loop(request)

    @mcp.tool(name="dotloop_get_loop_details", description="Get details for one Dotloop loop.")
    async def dotloop_get_loop_details(profile_id: int, loop_id: int) -> JsonObject:
        request = validate_request(ProfileLoopRequest, locals())
        return await adapter.get_loop_details(request)


def _register_folder_tools(mcp: FastMCP, adapter: DotloopToolAdapter) -> None:
    @mcp.tool(name="dotloop_list_folders", description="List folders for a Dotloop loop.")
    async def dotloop_list_folders(
        profile_id: int,
        loop_id: int,
        include_documents: bool = False,
        include_archived: bool = False,
    ) -> JsonObject:
        request = validate_request(ListFoldersToolInput, locals())
        return await adapter.list_folders(request)

    @mcp.tool(name="dotloop_get_folder", description="Get one Dotloop loop folder.")
    async def dotloop_get_folder(
        profile_id: int,
        loop_id: int,
        folder_id: int,
        include_documents: bool = False,
        include_archived: bool = False,
    ) -> JsonObject:
        request = validate_request(GetFolderToolInput, locals())
        return await adapter.get_folder(request)


def _register_document_tools(mcp: FastMCP, adapter: DotloopToolAdapter) -> None:
    @mcp.tool(name="dotloop_list_documents", description="List Dotloop loop documents.")
    async def dotloop_list_documents(
        profile_id: int,
        loop_id: int,
        folder_id: int | None = None,
    ) -> JsonObject:
        request = validate_request(ListDocumentsToolInput, locals())
        return await adapter.list_documents(request)

    @mcp.tool(name="dotloop_get_document", description="Get Dotloop document metadata.")
    async def dotloop_get_document(
        profile_id: int,
        loop_id: int,
        document_id: int,
        folder_id: int | None = None,
    ) -> JsonObject:
        request = validate_request(DocumentRequest, locals())
        return await adapter.get_document(request)

    @mcp.tool(
        name="dotloop_download_document",
        description="Download a Dotloop document as base64 with a byte-size limit.",
    )
    async def dotloop_download_document(
        profile_id: int,
        loop_id: int,
        document_id: int,
        folder_id: int | None = None,
        max_bytes: int = 5_000_000,
    ) -> JsonObject:
        request = validate_request(DownloadDocumentRequest, locals())
        return await adapter.download_document(request)


def _register_participant_tools(mcp: FastMCP, adapter: DotloopToolAdapter) -> None:
    @mcp.tool(name="dotloop_list_participants", description="List Dotloop loop participants.")
    async def dotloop_list_participants(profile_id: int, loop_id: int) -> JsonObject:
        request = validate_request(ProfileLoopRequest, locals())
        return await adapter.list_participants(request)

    @mcp.tool(name="dotloop_get_participant", description="Get one Dotloop loop participant.")
    async def dotloop_get_participant(
        profile_id: int,
        loop_id: int,
        participant_id: int,
    ) -> JsonObject:
        request = validate_request(ParticipantRequest, locals())
        return await adapter.get_participant(request)


def _register_task_tools(mcp: FastMCP, adapter: DotloopToolAdapter) -> None:
    @mcp.tool(name="dotloop_list_task_lists", description="List task lists for a Dotloop loop.")
    async def dotloop_list_task_lists(profile_id: int, loop_id: int) -> JsonObject:
        request = validate_request(ProfileLoopRequest, locals())
        return await adapter.list_task_lists(request)

    @mcp.tool(name="dotloop_get_task_list", description="Get one Dotloop task list.")
    async def dotloop_get_task_list(
        profile_id: int,
        loop_id: int,
        tasklist_id: int,
    ) -> JsonObject:
        request = validate_request(TaskListRequest, locals())
        return await adapter.get_task_list(request)

    @mcp.tool(name="dotloop_list_tasks", description="List Dotloop tasks in a task list.")
    async def dotloop_list_tasks(
        profile_id: int,
        loop_id: int,
        tasklist_id: int,
    ) -> JsonObject:
        request = validate_request(TaskListRequest, locals())
        return await adapter.list_tasks(request)

    @mcp.tool(name="dotloop_get_task", description="Get one Dotloop task.")
    async def dotloop_get_task(
        profile_id: int,
        loop_id: int,
        tasklist_id: int,
        task_id: int,
    ) -> JsonObject:
        request = validate_request(TaskRequest, locals())
        return await adapter.get_task(request)

    @mcp.tool(name="dotloop_get_task_summary", description="Get task summary for a Dotloop loop.")
    async def dotloop_get_task_summary(profile_id: int, loop_id: int) -> JsonObject:
        request = validate_request(ProfileLoopRequest, locals())
        return await adapter.get_task_summary(request)

    @mcp.tool(name="dotloop_get_all_tasks_in_loop", description="Get all tasks in a Dotloop loop.")
    async def dotloop_get_all_tasks_in_loop(profile_id: int, loop_id: int) -> JsonObject:
        request = validate_request(ProfileLoopRequest, locals())
        return await adapter.get_all_tasks_in_loop(request)

    @mcp.tool(name="dotloop_get_pending_tasks", description="Get pending tasks in a Dotloop loop.")
    async def dotloop_get_pending_tasks(profile_id: int, loop_id: int) -> JsonObject:
        request = validate_request(ProfileLoopRequest, locals())
        return await adapter.get_pending_tasks(request)

    @mcp.tool(
        name="dotloop_get_completed_tasks",
        description="Get completed tasks in a Dotloop loop.",
    )
    async def dotloop_get_completed_tasks(profile_id: int, loop_id: int) -> JsonObject:
        request = validate_request(ProfileLoopRequest, locals())
        return await adapter.get_completed_tasks(request)


def _register_activity_tools(mcp: FastMCP, adapter: DotloopToolAdapter) -> None:
    @mcp.tool(name="dotloop_list_loop_activity", description="List Dotloop loop activity.")
    async def dotloop_list_loop_activity(
        profile_id: int,
        loop_id: int,
        batch_size: int = 100,
        batch_number: int = 1,
    ) -> JsonObject:
        request = validate_request(ListActivityToolInput, locals())
        return await adapter.list_loop_activity(request)

    @mcp.tool(name="dotloop_get_recent_activity", description="Get recent Dotloop loop activity.")
    async def dotloop_get_recent_activity(
        profile_id: int,
        loop_id: int,
        limit: int = 10,
    ) -> JsonObject:
        request = validate_request(RecentActivityToolInput, locals())
        return await adapter.get_recent_activity(request)

    @mcp.tool(name="dotloop_get_activity_summary", description="Get Dotloop activity summary.")
    async def dotloop_get_activity_summary(profile_id: int, loop_id: int) -> JsonObject:
        request = validate_request(ProfileLoopRequest, locals())
        return await adapter.get_activity_summary(request)

    @mcp.tool(
        name="dotloop_get_activity_by_type",
        description="Get Dotloop loop activity filtered by type.",
    )
    async def dotloop_get_activity_by_type(
        profile_id: int,
        loop_id: int,
        activity_type: str,
        batch_size: int | None = None,
    ) -> JsonObject:
        request = validate_request(ActivityByTypeToolInput, locals())
        return await adapter.get_activity_by_type(request)

    @mcp.tool(
        name="dotloop_get_activity_by_user",
        description="Get Dotloop loop activity filtered by user.",
    )
    async def dotloop_get_activity_by_user(
        profile_id: int,
        loop_id: int,
        user_name: str,
        batch_size: int | None = None,
    ) -> JsonObject:
        request = validate_request(ActivityByUserToolInput, locals())
        return await adapter.get_activity_by_user(request)


def _register_template_tools(mcp: FastMCP, adapter: DotloopToolAdapter) -> None:
    @mcp.tool(name="dotloop_list_loop_templates", description="List Dotloop loop templates.")
    async def dotloop_list_loop_templates(profile_id: int) -> JsonObject:
        request = validate_request(ProfileIdRequest, locals())
        return await adapter.list_loop_templates(request)

    @mcp.tool(name="dotloop_get_loop_template", description="Get one Dotloop loop template.")
    async def dotloop_get_loop_template(profile_id: int, template_id: int) -> JsonObject:
        request = validate_request(TemplateRequest, locals())
        return await adapter.get_loop_template(request)

    @mcp.tool(name="dotloop_find_template_by_name", description="Find a Dotloop template by name.")
    async def dotloop_find_template_by_name(
        profile_id: int,
        template_name: str,
        exact_match: bool = True,
    ) -> JsonObject:
        request = validate_request(FindTemplateToolInput, locals())
        return await adapter.find_template_by_name(request)

    @mcp.tool(
        name="dotloop_get_template_summary",
        description="Get Dotloop template summary for a profile.",
    )
    async def dotloop_get_template_summary(profile_id: int) -> JsonObject:
        request = validate_request(ProfileIdRequest, locals())
        return await adapter.get_template_summary(request)

    @mcp.tool(name="dotloop_get_templates_by_type", description="Get Dotloop templates by type.")
    async def dotloop_get_templates_by_type(profile_id: int, template_type: str) -> JsonObject:
        request = validate_request(TemplateTypeToolInput, locals())
        return await adapter.get_templates_by_type(request)

    @mcp.tool(name="dotloop_get_default_templates", description="Get default Dotloop templates.")
    async def dotloop_get_default_templates(profile_id: int) -> JsonObject:
        request = validate_request(ProfileIdRequest, locals())
        return await adapter.get_default_templates(request)

    @mcp.tool(name="dotloop_get_custom_templates", description="Get custom Dotloop templates.")
    async def dotloop_get_custom_templates(profile_id: int) -> JsonObject:
        request = validate_request(ProfileIdRequest, locals())
        return await adapter.get_custom_templates(request)


def _register_resources(mcp: FastMCP, *, project_root: Path) -> None:
    @mcp.resource(
        COVERAGE_RESOURCE_URI,
        name="Dotloop API coverage matrix",
        description="Dotloop library-to-MCP coverage matrix.",
        mime_type="text/markdown",
    )
    def dotloop_api_coverage_matrix() -> str:
        docs_path = project_root / "docs" / "api" / "dotloop-api-coverage-matrix.md"
        if docs_path.exists():
            return docs_path.read_text()
        return API_COVERAGE_MARKDOWN

    @mcp.resource(
        METHOD_COVERAGE_RESOURCE_URI,
        name="Dotloop library method coverage",
        description="Method-level Dotloop library-to-MCP exposure matrix.",
        mime_type="text/markdown",
    )
    def dotloop_library_method_coverage() -> str:
        docs_path = project_root / "docs" / "api" / "dotloop-library-method-coverage.md"
        if docs_path.exists():
            return docs_path.read_text()
        return METHOD_COVERAGE_MARKDOWN
