from dataclasses import dataclass, fields
from typing import Dict, List, Optional

from pyodk.errors import PyODKError
from pyodk.session import ClientSession
from pyodk.utils import coalesce


@dataclass
class ProjectEntity:

    id: int
    name: str
    description: str
    keyId: int
    archived: bool
    createdAt: str
    updatedAt: str
    deletedAt: str
    appUsers: int
    forms: int
    lastSubmission: str


class ProjectService:
    def __init__(self, session: ClientSession, default_project_id: Optional[int] = None):
        self.session: ClientSession = session
        self.default_project_id: Optional[int] = default_project_id

    def _validate_project_id(self, project_id: Optional[int] = None) -> int:
        pid = coalesce(project_id, self.default_project_id)
        if pid is None:
            msg = "No project ID was provided, either directly or via a default setting."
            raise PyODKError(msg)
        return pid

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
            raise PyODKError(msg)

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
            raise PyODKError(msg)

    def read(self, project_id: Optional[int] = None) -> ProjectEntity:
        """
        Read the details of a Project.

        :param project_id: The id of the project to read.
        """
        pid = self._validate_project_id(project_id=project_id)
        raw = self._read_request(project_id=pid)
        return ProjectEntity(**{f.name: raw.get(f.name) for f in fields(ProjectEntity)})
