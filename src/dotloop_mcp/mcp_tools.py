"""MCP adapter and request models for Dotloop tools."""

from __future__ import annotations

from pydantic import Field

from dotloop_mcp.models.common import (
    DocumentRequest,
    DownloadDocumentRequest,
    FolderRequest,
    JsonObject,
    ParticipantRequest,
    ProfileIdRequest,
    ProfileLoopRequest,
    StrictRequestModel,
    TaskListRequest,
    TaskRequest,
    TemplateRequest,
)
from dotloop_mcp.services import DotloopService


class ListLoopsToolInput(ProfileIdRequest):
    """Input for loop listing."""

    batch_size: int = Field(default=100, gt=0, le=500)
    batch_number: int = Field(default=1, gt=0)
    sort: str | None = None
    include_details: bool = False


class ListFoldersToolInput(ProfileLoopRequest):
    """Input for folder listing."""

    include_documents: bool = False
    include_archived: bool = False


class GetFolderToolInput(FolderRequest):
    """Input for folder lookup."""

    include_documents: bool = False
    include_archived: bool = False


class ListDocumentsToolInput(ProfileLoopRequest):
    """Input for document listing."""

    folder_id: int | None = Field(default=None, gt=0)


class ListActivityToolInput(ProfileLoopRequest):
    """Input for activity listing."""

    batch_size: int = Field(default=100, gt=0, le=500)
    batch_number: int = Field(default=1, gt=0)


class RecentActivityToolInput(ProfileLoopRequest):
    """Input for recent activity lookup."""

    limit: int = Field(default=10, gt=0, le=100)


class FindTemplateToolInput(ProfileIdRequest):
    """Input for template name lookup."""

    template_name: str = Field(min_length=1)
    exact_match: bool = True


class DotloopToolAdapter:
    """Thin MCP adapter over Dotloop services."""

    def __init__(self, service: DotloopService) -> None:
        """Initialize the adapter.

        Args:
            service: Dotloop service adapter.
        """
        self._service = service

    async def get_account(self) -> JsonObject:
        """Get current Dotloop account."""
        return await self._service.get_account()

    async def list_profiles(self) -> JsonObject:
        """List Dotloop profiles."""
        return await self._service.list_profiles()

    async def get_profile(self, request: ProfileIdRequest) -> JsonObject:
        """Get a Dotloop profile."""
        return await self._service.get_profile(request.profile_id)

    async def list_loops(self, request: ListLoopsToolInput) -> JsonObject:
        """List Dotloop loops."""
        return await self._service.list_loops(
            request.profile_id,
            batch_size=request.batch_size,
            batch_number=request.batch_number,
            sort=request.sort,
            include_details=request.include_details,
        )

    async def get_loop(self, request: ProfileLoopRequest) -> JsonObject:
        """Get a Dotloop loop."""
        return await self._service.get_loop(request.profile_id, request.loop_id)

    async def get_loop_details(self, request: ProfileLoopRequest) -> JsonObject:
        """Get Dotloop loop details."""
        return await self._service.get_loop_details(request.profile_id, request.loop_id)

    async def list_folders(self, request: ListFoldersToolInput) -> JsonObject:
        """List loop folders."""
        return await self._service.list_folders(
            request.profile_id,
            request.loop_id,
            include_documents=request.include_documents,
            include_archived=request.include_archived,
        )

    async def get_folder(self, request: GetFolderToolInput) -> JsonObject:
        """Get a loop folder."""
        return await self._service.get_folder(
            request.profile_id,
            request.loop_id,
            request.folder_id,
            include_documents=request.include_documents,
            include_archived=request.include_archived,
        )

    async def list_documents(self, request: ListDocumentsToolInput) -> JsonObject:
        """List loop documents."""
        return await self._service.list_documents(
            request.profile_id,
            request.loop_id,
            folder_id=request.folder_id,
        )

    async def get_document(self, request: DocumentRequest) -> JsonObject:
        """Get document metadata."""
        return await self._service.get_document(
            request.profile_id,
            request.loop_id,
            request.document_id,
            folder_id=request.folder_id,
        )

    async def download_document(self, request: DownloadDocumentRequest) -> JsonObject:
        """Download a size-limited document."""
        return await self._service.download_document(
            request.profile_id,
            request.loop_id,
            request.document_id,
            folder_id=request.folder_id,
            max_bytes=request.max_bytes,
        )

    async def list_participants(self, request: ProfileLoopRequest) -> JsonObject:
        """List loop participants."""
        return await self._service.list_participants(request.profile_id, request.loop_id)

    async def get_participant(self, request: ParticipantRequest) -> JsonObject:
        """Get a loop participant."""
        return await self._service.get_participant(
            request.profile_id,
            request.loop_id,
            request.participant_id,
        )

    async def list_task_lists(self, request: ProfileLoopRequest) -> JsonObject:
        """List loop task lists."""
        return await self._service.list_task_lists(request.profile_id, request.loop_id)

    async def get_task_list(self, request: TaskListRequest) -> JsonObject:
        """Get a task list."""
        return await self._service.get_task_list(
            request.profile_id,
            request.loop_id,
            request.tasklist_id,
        )

    async def list_tasks(self, request: TaskListRequest) -> JsonObject:
        """List tasks."""
        return await self._service.list_tasks(
            request.profile_id,
            request.loop_id,
            request.tasklist_id,
        )

    async def get_task(self, request: TaskRequest) -> JsonObject:
        """Get a task."""
        return await self._service.get_task(
            request.profile_id,
            request.loop_id,
            request.tasklist_id,
            request.task_id,
        )

    async def get_task_summary(self, request: ProfileLoopRequest) -> JsonObject:
        """Get loop task summary."""
        return await self._service.get_task_summary(request.profile_id, request.loop_id)

    async def list_loop_activity(self, request: ListActivityToolInput) -> JsonObject:
        """List loop activity."""
        return await self._service.list_loop_activity(
            request.profile_id,
            request.loop_id,
            batch_size=request.batch_size,
            batch_number=request.batch_number,
        )

    async def get_recent_activity(self, request: RecentActivityToolInput) -> JsonObject:
        """Get recent loop activity."""
        return await self._service.get_recent_activity(
            request.profile_id,
            request.loop_id,
            request.limit,
        )

    async def get_activity_summary(self, request: ProfileLoopRequest) -> JsonObject:
        """Get loop activity summary."""
        return await self._service.get_activity_summary(request.profile_id, request.loop_id)

    async def list_loop_templates(self, request: ProfileIdRequest) -> JsonObject:
        """List loop templates."""
        return await self._service.list_loop_templates(request.profile_id)

    async def get_loop_template(self, request: TemplateRequest) -> JsonObject:
        """Get loop template."""
        return await self._service.get_loop_template(request.profile_id, request.template_id)

    async def find_template_by_name(self, request: FindTemplateToolInput) -> JsonObject:
        """Find template by name."""
        return await self._service.find_template_by_name(
            request.profile_id,
            request.template_name,
            exact_match=request.exact_match,
        )

    async def get_template_summary(self, request: ProfileIdRequest) -> JsonObject:
        """Get template summary."""
        return await self._service.get_template_summary(request.profile_id)


def validate_request[ModelT: StrictRequestModel](
    model_type: type[ModelT],
    values: dict[str, object],
) -> ModelT:
    """Validate MCP tool locals into a strict model."""
    return model_type.model_validate(
        {key: value for key, value in values.items() if key in model_type.model_fields}
    )
