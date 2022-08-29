import logging
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Dict, List, Optional

from pyodk import validators
from pyodk.errors import PyODKError
from pyodk.session import ClientSession
from pyodk.utils import STRPTIME_FMT_UTC

log = logging.getLogger(__name__)


@dataclass
class ProjectEntity:

    id: int
    name: str
    description: str
    keyId: int
    archived: bool
    createdAt: datetime
    appUsers: Optional[int] = None
    forms: Optional[int] = None
    lastSubmission: Optional[str] = None
    updatedAt: Optional[datetime] = None
    deletedAt: Optional[datetime] = None

    def __post_init__(self):
        # Convert date strings to datetime objects.
        dt_fields = ["createdAt", "updatedAt", "deletedAt"]
        for d in dt_fields:
            dt_value = getattr(self, d)
            if isinstance(dt_value, str):
                setattr(self, d, datetime.strptime(dt_value, STRPTIME_FMT_UTC))


class ProjectService:
    def __init__(self, session: ClientSession, default_project_id: Optional[int] = None):
        self.session: ClientSession = session
        self.default_project_id: Optional[int] = default_project_id

    def _read_all_request(self) -> List[Dict]:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects",
        )
        if response.status_code == 200:
            return response.json()
        else:
            msg = (
                f"The project listing request failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            err = PyODKError(msg)
            log.error(err, exc_info=True)
            raise err

    def read_all(self) -> List[ProjectEntity]:
        """
        Read the details of all projects.
        """
        raw = self._read_all_request()
        return [
            ProjectEntity(**{f.name: r.get(f.name) for f in fields(ProjectEntity)})
            for r in raw
        ]

    def _read_request(self, project_id: int) -> Dict:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}",
        )
        if response.status_code == 200:
            return response.json()
        else:
            msg = (
                f"The project read request failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            err = PyODKError(msg)
            log.error(err, exc_info=True)
            raise err

    def read(self, project_id: Optional[int] = None) -> ProjectEntity:
        """
        Read the details of a Project.

        :param project_id: The id of the project to read.
        """
        try:
            pid = validators.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            raw = self._read_request(project_id=pid)
            return ProjectEntity(
                **{f.name: raw.get(f.name) for f in fields(ProjectEntity)}
            )
