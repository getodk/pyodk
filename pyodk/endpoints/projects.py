import logging
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from pyodk import validators as pv
from pyodk.endpoints import bases, utils
from pyodk.endpoints.forms import FormService
from pyodk.errors import PyODKError
from pyodk.session import ClientSession

log = logging.getLogger(__name__)


class Project(bases.Model):
    m: "ProjectManager" = Field(repr=False, exclude=True)

    id: int
    name: str
    createdAt: datetime
    description: Optional[str]
    archived: Optional[bool]
    keyId: Optional[int]
    appUsers: Optional[int]
    forms: Optional[int]
    lastSubmission: Optional[str]
    updatedAt: Optional[datetime]
    deletedAt: Optional[datetime]


class ProjectManager(bases.Manager):
    __slots__ = ("session", "project_id", "_projects", "_forms")

    def __init__(
        self,
        session: ClientSession,
        project_id: int,
    ):
        self.session: ClientSession = session
        self.project_id: int = project_id
        self._projects: Optional[ProjectService] = None
        self._forms: Optional[FormService] = None

    @property
    def projects(self) -> "ProjectService":
        if self._projects is None:
            self._projects = ProjectService(
                session=self.session,
                default_project_id=self.project_id,
            )
        return self._projects

    @property
    def forms(self) -> "FormService":
        if self._forms is None:
            self._forms = FormService(
                session=self.session,
                default_project_id=self.project_id,
            )
        return self._forms

    @classmethod
    def from_dict(
        cls,
        session: ClientSession,
        project_id: int,
        data: Dict,
    ) -> Project:
        mgr = cls(session=session, project_id=project_id)
        return Project(m=mgr, **data)


Project.update_forward_refs()


class ProjectService(bases.Service):
    def __init__(self, session: ClientSession, default_project_id: Optional[int] = None):
        self.session: ClientSession = session
        self.default_project_id: Optional[int] = default_project_id

    def _read_all_request(self) -> List[Dict]:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects",
        )
        return utils.error_if_not_200(
            response=response, log=log, action="project listing"
        )

    def read_all(self) -> List[Project]:
        """
        Read the details of all projects.
        """
        raw = self._read_all_request()
        return [
            ProjectManager.from_dict(
                session=self.session,
                project_id=r["id"],
                data=r,
            )
            for r in raw
        ]

    def _read_request(self, project_id: int) -> Dict:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}",
        )
        return utils.error_if_not_200(response=response, log=log, action="project read")

    def read(self, project_id: Optional[int] = None) -> Project:
        """
        Read the details of a Project.

        :param project_id: The id of the project to read.
        """
        try:
            pid = pv.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            raw = self._read_request(project_id=pid)
            return ProjectManager.from_dict(
                session=self.session,
                project_id=raw["id"],
                data=raw,
            )
