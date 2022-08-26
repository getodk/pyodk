from dataclasses import dataclass, fields
from typing import Dict, List, Optional

from pyodk.errors import PyODKError
from pyodk.session import ClientSession
from pyodk.utils import coalesce


@dataclass
class SubmissionEntity:

    instanceId: str
    instanceName: str
    submitterId: int
    deviceId: str
    userAgent: str
    reviewState: str  # null, edited, hasIssues, rejected, approved
    createdAt: str
    updatedAt: str


class SubmissionService:
    def __init__(self, session: ClientSession, default_project_id: Optional[int] = None):
        self.session: ClientSession = session
        self.default_project_id: Optional[int] = default_project_id

    def _validate_project_id(self, project_id: Optional[int] = None) -> int:
        pid = coalesce(project_id, self.default_project_id)
        if pid is None:
            msg = "No project ID was provided, either directly or via a default setting."
            raise PyODKError(msg)
        return pid

    @staticmethod
    def _validate_form_id(form_id: Optional[str] = None) -> str:
        if form_id is None:
            msg = "No form ID was provided."
            raise PyODKError(msg)
        return form_id

    @staticmethod
    def _validate_instance_id(instance_id: Optional[str] = None) -> str:
        if instance_id is None:
            msg = "No instance ID was provided."
            raise PyODKError(msg)
        return instance_id

    def _read_all_request(self, project_id: int, form_id: str) -> List[Dict]:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}/forms/{form_id}"
            f"/submissions",
        )
        if response.status_code == 200:
            return response.json()
        else:
            msg = (
                f"The submission listing request failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            raise PyODKError(msg)

    def read_all(
        self, form_id: str, project_id: Optional[int] = None
    ) -> List[SubmissionEntity]:
        """
        Read the details of all Submissions.

        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project the Submissions belong to.
        """
        pid = self._validate_project_id(project_id=project_id)
        fid = self._validate_form_id(form_id=form_id)
        raw = self._read_all_request(project_id=pid, form_id=fid)
        return [
            SubmissionEntity(**{f.name: r.get(f.name) for f in fields(SubmissionEntity)})
            for r in raw
        ]

    def _read_request(self, project_id: int, form_id: str, instance_id: str) -> Dict:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}/forms/{form_id}"
            f"/submissions/{instance_id}"
        )
        if response.status_code == 200:
            return response.json()
        else:
            msg = (
                f"The submission read request failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            raise PyODKError(msg)

    def read(
        self,
        form_id: str,
        instance_id: str,
        project_id: Optional[int] = None,
    ) -> SubmissionEntity:
        """
        Read the details of a Submission.

        :param form_id: The xmlFormId of the Form being referenced.
        :param instance_id: The instanceId of the Submission being referenced.
        :param project_id: The id of the project this form belongs to.
        """
        pid = self._validate_project_id(project_id=project_id)
        fid = self._validate_form_id(form_id=form_id)
        iid = self._validate_instance_id(instance_id=instance_id)
        raw = self._read_request(project_id=pid, form_id=fid, instance_id=iid)
        return SubmissionEntity(
            **{f.name: raw.get(f.name) for f in fields(SubmissionEntity)}
        )
