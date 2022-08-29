import logging
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Dict, List, Optional

from pyodk import validators
from pyodk.endpoints.utils import error_if_not_200
from pyodk.errors import PyODKError
from pyodk.session import ClientSession
from pyodk.utils import STRPTIME_FMT_UTC

log = logging.getLogger(__name__)


@dataclass
class SubmissionEntity:

    instanceId: str
    submitterId: int
    deviceId: str
    createdAt: str
    reviewState: Optional[str] = None  # null, edited, hasIssues, rejected, approved
    userAgent: Optional[str] = None
    instanceName: Optional[str] = None
    updatedAt: Optional[datetime] = None

    def __post_init__(self):
        # Convert date strings to datetime objects.
        dt_fields = ["createdAt", "updatedAt"]
        for d in dt_fields:
            dt_value = getattr(self, d)
            if isinstance(dt_value, str):
                setattr(self, d, datetime.strptime(dt_value, STRPTIME_FMT_UTC))


class SubmissionService:
    def __init__(self, session: ClientSession, default_project_id: Optional[int] = None):
        self.session: ClientSession = session
        self.default_project_id: Optional[int] = default_project_id

    def _read_all_request(self, project_id: int, form_id: str) -> List[Dict]:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}/forms/{form_id}"
            f"/submissions",
        )
        return error_if_not_200(response=response, log=log, action="submission listing")

    def read_all(
        self, form_id: str, project_id: Optional[int] = None
    ) -> List[SubmissionEntity]:
        """
        Read the details of all Submissions.

        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project the Submissions belong to.
        """
        try:
            pid = validators.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
            fid = validators.validate_form_id(form_id=form_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            raw = self._read_all_request(project_id=pid, form_id=fid)
            return [
                SubmissionEntity(
                    **{f.name: r.get(f.name) for f in fields(SubmissionEntity)}
                )
                for r in raw
            ]

    def _read_request(self, project_id: int, form_id: str, instance_id: str) -> Dict:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}/forms/{form_id}"
            f"/submissions/{instance_id}"
        )
        return error_if_not_200(response=response, log=log, action="submission read")

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
        try:
            pid = validators.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
            fid = validators.validate_form_id(form_id=form_id)
            iid = validators.validate_instance_id(instance_id=instance_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            raw = self._read_request(project_id=pid, form_id=fid, instance_id=iid)
            return SubmissionEntity(
                **{f.name: raw.get(f.name) for f in fields(SubmissionEntity)}
            )
