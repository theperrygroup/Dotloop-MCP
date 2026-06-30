"""Deterministic Dotloop client fixtures for AI battle testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _loop(profile_id: int, loop_id: int) -> dict[str, Any]:
    return {
        "id": loop_id,
        "profileId": profile_id,
        "name": f"Battle Test Loop {loop_id}",
        "status": "ACTIVE",
        "transactionType": "PURCHASE_OFFER",
        "propertyAddress": {
            "street": f"{loop_id} Fixture Way",
            "city": "Salt Lake City",
            "state": "UT",
            "zipCode": "84101",
        },
    }


class BattleAccountClient:
    """Fixture account domain."""

    def get_account(self) -> dict[str, Any]:
        """Return deterministic account data."""
        return {
            "data": {
                "id": 9001,
                "firstName": "Avery",
                "lastName": "Battle",
                "email": "avery.battle@example.test",
            }
        }


class BattleProfileClient:
    """Fixture profile domain."""

    def list_profiles(self) -> dict[str, Any]:
        """Return deterministic profile data."""
        return {
            "data": [
                {"id": 101, "name": "TPG Battle Main"},
                {"id": 102, "name": "TPG Battle Team"},
            ]
        }

    def get_profile(self, profile_id: int) -> dict[str, Any]:
        """Return one deterministic profile."""
        names = {101: "TPG Battle Main", 102: "TPG Battle Team"}
        return {"data": {"id": profile_id, "name": names.get(profile_id, "Fixture Profile")}}


class BattleLoopClient:
    """Fixture loop domain."""

    def list_loops(
        self,
        profile_id: int,
        batch_size: int = 100,
        batch_number: int = 1,
        sort: str | None = None,
        include_details: bool = False,
    ) -> dict[str, Any]:
        """Return deterministic loops for a profile."""
        loops = [_loop(profile_id, 201), _loop(profile_id, 202)]
        if include_details:
            for item in loops:
                item["details"] = {"source": "battle-fixture", "sort": sort}
        return {
            "data": loops[:batch_size],
            "meta": {"batchSize": batch_size, "batchNumber": batch_number, "sort": sort},
        }

    def get_loop(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        """Return one deterministic loop."""
        return {"data": _loop(profile_id, loop_id)}


class BattleLoopDetailClient:
    """Fixture loop detail domain."""

    def get_loop_details(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        """Return deterministic loop details."""
        return {
            "data": {
                "profileId": profile_id,
                "loopId": loop_id,
                "purchasePrice": 650000,
                "contractDate": "2026-06-30",
                "closingDate": "2026-07-31",
                "fixture": True,
            }
        }


class BattleFolderClient:
    """Fixture folder domain."""

    def list_folders(
        self,
        profile_id: int,
        loop_id: int,
        include_documents: bool = False,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        """Return deterministic folders."""
        folders: list[dict[str, Any]] = [
            {"id": 301, "profileId": profile_id, "loopId": loop_id, "name": "Contracts"},
            {"id": 302, "profileId": profile_id, "loopId": loop_id, "name": "Disclosures"},
        ]
        if include_documents:
            folders[0]["documents"] = [{"id": 401, "name": "Buyer REPC.pdf"}]
        if include_archived:
            folders.append(
                {"id": 399, "profileId": profile_id, "loopId": loop_id, "name": "Archived"}
            )
        return {"data": folders}

    def get_folder(
        self,
        profile_id: int,
        loop_id: int,
        folder_id: int,
        include_documents: bool = False,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        """Return one deterministic folder."""
        folder: dict[str, Any] = {
            "id": folder_id,
            "profileId": profile_id,
            "loopId": loop_id,
            "name": "Contracts",
            "includeArchived": include_archived,
        }
        if include_documents:
            folder["documents"] = [{"id": 401, "name": "Buyer REPC.pdf"}]
        return {"data": folder}


class BattleDocumentClient:
    """Fixture document domain."""

    def list_documents(
        self,
        profile_id: int,
        loop_id: int,
        folder_id: int | None = None,
    ) -> dict[str, Any]:
        """Return deterministic document metadata."""
        return {
            "data": [
                {
                    "id": 401,
                    "profileId": profile_id,
                    "loopId": loop_id,
                    "folderId": folder_id,
                    "name": "Buyer REPC.pdf",
                    "mimeType": "application/pdf",
                },
                {
                    "id": 402,
                    "profileId": profile_id,
                    "loopId": loop_id,
                    "folderId": folder_id,
                    "name": "Seller Disclosures.pdf",
                    "mimeType": "application/pdf",
                },
            ]
        }

    def get_document(
        self,
        profile_id: int,
        loop_id: int,
        document_id: int,
        folder_id: int | None = None,
    ) -> dict[str, Any]:
        """Return one deterministic document."""
        return {
            "data": {
                "id": document_id,
                "profileId": profile_id,
                "loopId": loop_id,
                "folderId": folder_id,
                "name": f"Fixture Document {document_id}.pdf",
                "mimeType": "application/pdf",
                "sizeBytes": 128,
            }
        }

    def download_document(
        self,
        profile_id: int,
        loop_id: int,
        document_id: int,
        folder_id: int | None = None,
    ) -> bytes:
        """Return deterministic document bytes without touching the network."""
        return f"battle-pdf:{profile_id}:{loop_id}:{document_id}:{folder_id}".encode()


class BattleParticipantClient:
    """Fixture participant domain."""

    def list_participants(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        """Return deterministic participants."""
        return {
            "data": [
                {
                    "id": 501,
                    "profileId": profile_id,
                    "loopId": loop_id,
                    "fullName": "Jordan Buyer",
                    "role": "Buyer",
                },
                {
                    "id": 502,
                    "profileId": profile_id,
                    "loopId": loop_id,
                    "fullName": "Casey Seller",
                    "role": "Seller",
                },
            ]
        }

    def get_participant(self, profile_id: int, loop_id: int, participant_id: int) -> dict[str, Any]:
        """Return one deterministic participant."""
        return {
            "data": {
                "id": participant_id,
                "profileId": profile_id,
                "loopId": loop_id,
                "fullName": "Jordan Buyer",
                "role": "Buyer",
            }
        }


class BattleTaskClient:
    """Fixture task domain."""

    def list_task_lists(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        """Return deterministic task lists."""
        return {"data": [{"id": 601, "profileId": profile_id, "loopId": loop_id, "name": "REPC"}]}

    def get_task_list(self, profile_id: int, loop_id: int, tasklist_id: int) -> dict[str, Any]:
        """Return one deterministic task list."""
        return {"data": {"id": tasklist_id, "profileId": profile_id, "loopId": loop_id}}

    def list_tasks(self, profile_id: int, loop_id: int, tasklist_id: int) -> dict[str, Any]:
        """Return deterministic tasks."""
        return {
            "data": [
                {
                    "id": 701,
                    "tasklistId": tasklist_id,
                    "profileId": profile_id,
                    "loopId": loop_id,
                    "name": "Review REPC",
                    "status": "pending",
                },
                {
                    "id": 702,
                    "tasklistId": tasklist_id,
                    "profileId": profile_id,
                    "loopId": loop_id,
                    "name": "Send disclosures",
                    "status": "completed",
                },
            ]
        }

    def get_task(
        self,
        profile_id: int,
        loop_id: int,
        tasklist_id: int,
        task_id: int,
    ) -> dict[str, Any]:
        """Return one deterministic task."""
        return {
            "data": {
                "id": task_id,
                "tasklistId": tasklist_id,
                "profileId": profile_id,
                "loopId": loop_id,
                "name": "Review REPC",
                "status": "pending",
            }
        }

    def get_task_summary(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        """Return deterministic task summary."""
        return {"data": {"profileId": profile_id, "loopId": loop_id, "pending": 1, "completed": 1}}

    def get_all_tasks_in_loop(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        """Return all deterministic loop tasks."""
        return {"data": [{"profileId": profile_id, "loopId": loop_id, "scope": "all"}]}

    def get_pending_tasks(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        """Return deterministic pending tasks."""
        return {"data": [{"profileId": profile_id, "loopId": loop_id, "status": "pending"}]}

    def get_completed_tasks(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        """Return deterministic completed tasks."""
        return {"data": [{"profileId": profile_id, "loopId": loop_id, "status": "completed"}]}


class BattleActivityClient:
    """Fixture activity domain."""

    def list_loop_activity(
        self,
        profile_id: int,
        loop_id: int,
        batch_size: int = 100,
        batch_number: int = 1,
    ) -> dict[str, Any]:
        """Return deterministic activity rows."""
        return {
            "data": [
                {
                    "profileId": profile_id,
                    "loopId": loop_id,
                    "type": "Document",
                    "userName": "Avery Battle",
                    "batchSize": batch_size,
                    "batchNumber": batch_number,
                }
            ]
        }

    def get_recent_activity(self, profile_id: int, loop_id: int, limit: int = 10) -> dict[str, Any]:
        """Return deterministic recent activity."""
        return {"data": [{"profileId": profile_id, "loopId": loop_id, "limit": limit}]}

    def get_activity_summary(self, profile_id: int, loop_id: int) -> dict[str, Any]:
        """Return deterministic activity summary."""
        return {"data": {"profileId": profile_id, "loopId": loop_id, "Document": 1}}

    def get_activity_by_type(
        self,
        profile_id: int,
        loop_id: int,
        activity_type: str,
        batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Return deterministic type-filtered activity."""
        return {
            "data": [
                {
                    "profileId": profile_id,
                    "loopId": loop_id,
                    "activityType": activity_type,
                    "batchSize": batch_size,
                }
            ]
        }

    def get_activity_by_user(
        self,
        profile_id: int,
        loop_id: int,
        user_name: str,
        batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Return deterministic user-filtered activity."""
        return {
            "data": [
                {
                    "profileId": profile_id,
                    "loopId": loop_id,
                    "userName": user_name,
                    "batchSize": batch_size,
                }
            ]
        }


class BattleTemplateClient:
    """Fixture template domain."""

    def list_loop_templates(self, profile_id: int) -> dict[str, Any]:
        """Return deterministic templates."""
        return {
            "data": [
                {"id": 801, "profileId": profile_id, "name": "Buyer REPC", "type": "default"},
                {"id": 802, "profileId": profile_id, "name": "Lease Package", "type": "custom"},
            ]
        }

    def get_loop_template(self, profile_id: int, template_id: int) -> dict[str, Any]:
        """Return one deterministic template."""
        return {"data": {"id": template_id, "profileId": profile_id, "name": "Buyer REPC"}}

    def find_template_by_name(
        self,
        profile_id: int,
        template_name: str,
        exact_match: bool = True,
    ) -> dict[str, Any]:
        """Return a deterministic template name lookup."""
        return {
            "data": {
                "id": 801,
                "profileId": profile_id,
                "name": template_name,
                "exactMatch": exact_match,
            }
        }

    def get_template_summary(self, profile_id: int) -> dict[str, Any]:
        """Return deterministic template summary."""
        return {"data": {"profileId": profile_id, "templates": 2, "default": 1, "custom": 1}}

    def get_templates_by_type(self, profile_id: int, template_type: str) -> dict[str, Any]:
        """Return deterministic type-filtered templates."""
        return {"data": [{"id": 801, "profileId": profile_id, "templateType": template_type}]}

    def get_default_templates(self, profile_id: int) -> dict[str, Any]:
        """Return deterministic default templates."""
        return {"data": [{"id": 801, "profileId": profile_id, "templateScope": "default"}]}

    def get_custom_templates(self, profile_id: int) -> dict[str, Any]:
        """Return deterministic custom templates."""
        return {"data": [{"id": 802, "profileId": profile_id, "templateScope": "custom"}]}


@dataclass(frozen=True)
class BattleFixtureDotloopClient:
    """Dotloop-client-shaped fixture that never performs external I/O."""

    account: BattleAccountClient = field(default_factory=BattleAccountClient)
    profile: BattleProfileClient = field(default_factory=BattleProfileClient)
    loop: BattleLoopClient = field(default_factory=BattleLoopClient)
    loop_detail: BattleLoopDetailClient = field(default_factory=BattleLoopDetailClient)
    folder: BattleFolderClient = field(default_factory=BattleFolderClient)
    document: BattleDocumentClient = field(default_factory=BattleDocumentClient)
    participant: BattleParticipantClient = field(default_factory=BattleParticipantClient)
    task: BattleTaskClient = field(default_factory=BattleTaskClient)
    activity: BattleActivityClient = field(default_factory=BattleActivityClient)
    template: BattleTemplateClient = field(default_factory=BattleTemplateClient)
