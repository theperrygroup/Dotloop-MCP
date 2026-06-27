"""Async-safe service adapter around the synchronous `dotloop` package."""

from __future__ import annotations

import base64
from collections.abc import Callable
from typing import Any

import anyio

from dotloop_mcp.errors import DotloopMCPError, map_dotloop_exception
from dotloop_mcp.models.common import JsonObject, to_json_object


class DotloopService:
    """Read-first service adapter around a `dotloop.DotloopClient`-like object."""

    def __init__(self, client: Any) -> None:
        """Initialize the service.

        Args:
            client: Dotloop client or test double exposing the expected domains.
        """
        self._client = client

    async def _call_json(self, operation: Callable[[], object]) -> JsonObject:
        try:
            result = await anyio.to_thread.run_sync(operation)
        except Exception as exc:
            raise map_dotloop_exception(exc) from None
        return to_json_object(result)

    async def _call_bytes(self, operation: Callable[[], object]) -> bytes:
        try:
            result = await anyio.to_thread.run_sync(operation)
        except Exception as exc:
            raise map_dotloop_exception(exc) from None
        if not isinstance(result, bytes):
            raise DotloopMCPError("Dotloop document download did not return bytes.")
        return result

    async def get_account(self) -> JsonObject:
        """Get the current Dotloop account."""
        return await self._call_json(self._client.account.get_account)

    async def list_profiles(self) -> JsonObject:
        """List Dotloop profiles."""
        return await self._call_json(self._client.profile.list_profiles)

    async def get_profile(self, profile_id: int) -> JsonObject:
        """Get a Dotloop profile."""
        return await self._call_json(lambda: self._client.profile.get_profile(profile_id))

    async def list_loops(
        self,
        profile_id: int,
        *,
        batch_size: int = 100,
        batch_number: int = 1,
        sort: str | None = None,
        include_details: bool = False,
    ) -> JsonObject:
        """List loops for a profile."""
        return await self._call_json(
            lambda: self._client.loop.list_loops(
                profile_id=profile_id,
                batch_size=batch_size,
                batch_number=batch_number,
                sort=sort,
                include_details=include_details,
            )
        )

    async def get_loop(self, profile_id: int, loop_id: int) -> JsonObject:
        """Get a loop."""
        return await self._call_json(lambda: self._client.loop.get_loop(profile_id, loop_id))

    async def get_loop_details(self, profile_id: int, loop_id: int) -> JsonObject:
        """Get loop details."""
        return await self._call_json(
            lambda: self._client.loop_detail.get_loop_details(profile_id, loop_id)
        )

    async def list_folders(
        self,
        profile_id: int,
        loop_id: int,
        *,
        include_documents: bool = False,
        include_archived: bool = False,
    ) -> JsonObject:
        """List folders for a loop."""
        return await self._call_json(
            lambda: self._client.folder.list_folders(
                profile_id=profile_id,
                loop_id=loop_id,
                include_documents=include_documents,
                include_archived=include_archived,
            )
        )

    async def get_folder(
        self,
        profile_id: int,
        loop_id: int,
        folder_id: int,
        *,
        include_documents: bool = False,
        include_archived: bool = False,
    ) -> JsonObject:
        """Get a loop folder."""
        return await self._call_json(
            lambda: self._client.folder.get_folder(
                profile_id=profile_id,
                loop_id=loop_id,
                folder_id=folder_id,
                include_documents=include_documents,
                include_archived=include_archived,
            )
        )

    async def list_documents(
        self,
        profile_id: int,
        loop_id: int,
        *,
        folder_id: int | None = None,
    ) -> JsonObject:
        """List documents for a loop or folder."""
        return await self._call_json(
            lambda: self._client.document.list_documents(
                profile_id=profile_id,
                loop_id=loop_id,
                folder_id=folder_id,
            )
        )

    async def get_document(
        self,
        profile_id: int,
        loop_id: int,
        document_id: int,
        *,
        folder_id: int | None = None,
    ) -> JsonObject:
        """Get document metadata."""
        return await self._call_json(
            lambda: self._client.document.get_document(
                profile_id=profile_id,
                loop_id=loop_id,
                document_id=document_id,
                folder_id=folder_id,
            )
        )

    async def download_document(
        self,
        profile_id: int,
        loop_id: int,
        document_id: int,
        *,
        folder_id: int | None = None,
        max_bytes: int = 5_000_000,
    ) -> JsonObject:
        """Download a document as base64 with a size cap."""
        content = await self._call_bytes(
            lambda: self._client.document.download_document(
                profile_id=profile_id,
                loop_id=loop_id,
                document_id=document_id,
                folder_id=folder_id,
            )
        )
        if len(content) > max_bytes:
            raise DotloopMCPError(
                f"Dotloop document is {len(content)} bytes, exceeding the {max_bytes} byte limit."
            )
        return {
            "documentId": document_id,
            "sizeBytes": len(content),
            "contentType": "application/pdf",
            "contentBase64": base64.b64encode(content).decode("ascii"),
        }

    async def list_participants(self, profile_id: int, loop_id: int) -> JsonObject:
        """List loop participants."""
        return await self._call_json(
            lambda: self._client.participant.list_participants(profile_id, loop_id)
        )

    async def get_participant(
        self,
        profile_id: int,
        loop_id: int,
        participant_id: int,
    ) -> JsonObject:
        """Get a loop participant."""
        return await self._call_json(
            lambda: self._client.participant.get_participant(profile_id, loop_id, participant_id)
        )

    async def list_task_lists(self, profile_id: int, loop_id: int) -> JsonObject:
        """List task lists for a loop."""
        return await self._call_json(lambda: self._client.task.list_task_lists(profile_id, loop_id))

    async def get_task_list(self, profile_id: int, loop_id: int, tasklist_id: int) -> JsonObject:
        """Get a task list."""
        return await self._call_json(
            lambda: self._client.task.get_task_list(profile_id, loop_id, tasklist_id)
        )

    async def list_tasks(self, profile_id: int, loop_id: int, tasklist_id: int) -> JsonObject:
        """List tasks in a task list."""
        return await self._call_json(
            lambda: self._client.task.list_tasks(profile_id, loop_id, tasklist_id)
        )

    async def get_task(
        self,
        profile_id: int,
        loop_id: int,
        tasklist_id: int,
        task_id: int,
    ) -> JsonObject:
        """Get a task."""
        return await self._call_json(
            lambda: self._client.task.get_task(profile_id, loop_id, tasklist_id, task_id)
        )

    async def get_task_summary(self, profile_id: int, loop_id: int) -> JsonObject:
        """Get task summary for a loop."""
        return await self._call_json(
            lambda: self._client.task.get_task_summary(profile_id, loop_id)
        )

    async def list_loop_activity(
        self,
        profile_id: int,
        loop_id: int,
        *,
        batch_size: int = 100,
        batch_number: int = 1,
    ) -> JsonObject:
        """List loop activity."""
        return await self._call_json(
            lambda: self._client.activity.list_loop_activity(
                profile_id=profile_id,
                loop_id=loop_id,
                batch_size=batch_size,
                batch_number=batch_number,
            )
        )

    async def get_recent_activity(
        self, profile_id: int, loop_id: int, limit: int = 10
    ) -> JsonObject:
        """Get recent loop activity."""
        return await self._call_json(
            lambda: self._client.activity.get_recent_activity(profile_id, loop_id, limit)
        )

    async def get_activity_summary(self, profile_id: int, loop_id: int) -> JsonObject:
        """Get loop activity summary."""
        return await self._call_json(
            lambda: self._client.activity.get_activity_summary(profile_id, loop_id)
        )

    async def list_loop_templates(self, profile_id: int) -> JsonObject:
        """List loop templates for a profile."""
        return await self._call_json(lambda: self._client.template.list_loop_templates(profile_id))

    async def get_loop_template(self, profile_id: int, template_id: int) -> JsonObject:
        """Get a loop template."""
        return await self._call_json(
            lambda: self._client.template.get_loop_template(profile_id, template_id)
        )

    async def find_template_by_name(
        self,
        profile_id: int,
        template_name: str,
        *,
        exact_match: bool = True,
    ) -> JsonObject:
        """Find a loop template by name."""
        return await self._call_json(
            lambda: self._client.template.find_template_by_name(
                profile_id,
                template_name,
                exact_match,
            )
        )

    async def get_template_summary(self, profile_id: int) -> JsonObject:
        """Get template summary for a profile."""
        return await self._call_json(lambda: self._client.template.get_template_summary(profile_id))
