"""Shared test fakes for Dotloop MCP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class AccountFake:
    def get_account(self) -> dict[str, Any]:
        return {"data": {"id": 1, "firstName": "Ada"}}


class ProfileFake:
    def list_profiles(self) -> dict[str, Any]:
        return {"data": [{"id": 10, "name": "Main"}]}

    def get_profile(self, profile_id: int) -> dict[str, Any]:
        return {"data": {"id": profile_id, "name": "Main"}}


class LoopFake:
    def list_loops(
        self,
        profile_id: int,
        batch_size: int = 100,
        batch_number: int = 1,
        sort: str | None = None,
        include_details: bool = False,
    ) -> dict[str, Any]:
        return {
            "data": [
                {
                    "id": 20,
                    "profileId": profile_id,
                    "batchSize": batch_size,
                    "batchNumber": batch_number,
                    "sort": sort,
                    "includeDetails": include_details,
                }
            ]
        }

    def get_loop(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        return {"data": {"id": loop_id, "profileId": profile_id}}


class LoopDetailFake:
    def get_loop_details(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        return {"data": {"profileId": profile_id, "loopId": loop_id, "details": {}}}


class FolderFake:
    def list_folders(
        self,
        profile_id: int,
        loop_id: int,
        include_documents: bool = False,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        return {
            "data": [
                {
                    "id": 30,
                    "profileId": profile_id,
                    "loopId": loop_id,
                    "includeDocuments": include_documents,
                    "includeArchived": include_archived,
                }
            ]
        }

    def get_folder(
        self,
        profile_id: int,
        loop_id: int,
        folder_id: int,
        include_documents: bool = False,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        return {
            "data": {
                "id": folder_id,
                "profileId": profile_id,
                "loopId": loop_id,
                "includeDocuments": include_documents,
                "includeArchived": include_archived,
            }
        }


class DocumentFake:
    def list_documents(
        self,
        profile_id: int,
        loop_id: int,
        folder_id: int | None = None,
    ) -> dict[str, Any]:
        return {
            "data": [{"id": 40, "profileId": profile_id, "loopId": loop_id, "folderId": folder_id}]
        }

    def get_document(
        self,
        profile_id: int,
        loop_id: int,
        document_id: int,
        folder_id: int | None = None,
    ) -> dict[str, Any]:
        return {
            "data": {
                "id": document_id,
                "profileId": profile_id,
                "loopId": loop_id,
                "folderId": folder_id,
            }
        }

    def download_document(
        self,
        profile_id: int,
        loop_id: int,
        document_id: int,
        folder_id: int | None = None,
    ) -> bytes:
        return f"pdf:{profile_id}:{loop_id}:{document_id}:{folder_id}".encode()


class ParticipantFake:
    def list_participants(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        return {"data": [{"id": 50, "profileId": profile_id, "loopId": loop_id}]}

    def get_participant(self, profile_id: int, loop_id: int, participant_id: int) -> dict[str, Any]:
        return {"data": {"id": participant_id, "profileId": profile_id, "loopId": loop_id}}


class TaskFake:
    def list_task_lists(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        return {"data": [{"id": 60, "profileId": profile_id, "loopId": loop_id}]}

    def get_task_list(self, profile_id: int, loop_id: int, tasklist_id: int) -> dict[str, Any]:
        return {"data": {"id": tasklist_id, "profileId": profile_id, "loopId": loop_id}}

    def list_tasks(self, profile_id: int, loop_id: int, tasklist_id: int) -> dict[str, Any]:
        return {
            "data": [
                {"id": 70, "tasklistId": tasklist_id, "profileId": profile_id, "loopId": loop_id}
            ]
        }

    def get_task(
        self,
        profile_id: int,
        loop_id: int,
        tasklist_id: int,
        task_id: int,
    ) -> dict[str, Any]:
        return {
            "data": {
                "id": task_id,
                "tasklistId": tasklist_id,
                "profileId": profile_id,
                "loopId": loop_id,
            }
        }

    def get_task_summary(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        return {"data": {"profileId": profile_id, "loopId": loop_id, "pending": 1, "completed": 2}}


class ActivityFake:
    def list_loop_activity(
        self,
        profile_id: int,
        loop_id: int,
        batch_size: int = 100,
        batch_number: int = 1,
    ) -> dict[str, Any]:
        return {
            "data": [
                {
                    "profileId": profile_id,
                    "loopId": loop_id,
                    "batchSize": batch_size,
                    "batchNumber": batch_number,
                }
            ]
        }

    def get_recent_activity(self, profile_id: int, loop_id: int, limit: int = 10) -> dict[str, Any]:
        return {"data": [{"profileId": profile_id, "loopId": loop_id, "limit": limit}]}

    def get_activity_summary(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        return {"data": {"profileId": profile_id, "loopId": loop_id, "count": 1}}


class TemplateFake:
    def list_loop_templates(self, profile_id: int) -> dict[str, Any]:
        return {"data": [{"id": 80, "profileId": profile_id, "name": "Buyer"}]}

    def get_loop_template(self, profile_id: int, template_id: int) -> dict[str, Any]:
        return {"data": {"id": template_id, "profileId": profile_id}}

    def find_template_by_name(
        self,
        profile_id: int,
        template_name: str,
        exact_match: bool = True,
    ) -> dict[str, Any]:
        return {
            "data": {
                "id": 80,
                "profileId": profile_id,
                "name": template_name,
                "exactMatch": exact_match,
            }
        }

    def get_template_summary(self, profile_id: int) -> dict[str, Any]:
        return {"data": {"profileId": profile_id, "templates": 1}}


@dataclass
class FakeDotloopClient:
    account: AccountFake = AccountFake()
    profile: ProfileFake = ProfileFake()
    loop: LoopFake = LoopFake()
    loop_detail: LoopDetailFake = LoopDetailFake()
    folder: FolderFake = FolderFake()
    document: DocumentFake = DocumentFake()
    participant: ParticipantFake = ParticipantFake()
    task: TaskFake = TaskFake()
    activity: ActivityFake = ActivityFake()
    template: TemplateFake = TemplateFake()
