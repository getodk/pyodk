import logging
from datetime import datetime
from typing import List, Optional

from pyodk import validators as pv
from pyodk.endpoints import bases
from pyodk.errors import PyODKError
from pyodk.session import Session

log = logging.getLogger(__name__)


class Project(bases.Model):
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


class URLs(bases.Model):
    class Config:
        frozen = True

    list: str = "projects"
    get: str = "projects/{project_id}"
    get_data: str = "projects/{project_id}/forms/{form_id}.svc/{table_name}"


class ProjectService(bases.Service):
    __slots__ = ("urls", "session", "default_project_id")

    def __init__(
        self,
        session: Session,
        default_project_id: Optional[int] = None,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session
        self.default_project_id: Optional[int] = default_project_id

    def list(self) -> List[Project]:
        """
        Read the details of all projects.
        """
        response = self.session.get_200_or_error(url=self.urls.list, logger=log)
        data = response.json()
        return [Project(**r) for r in data]

    def get(self, project_id: Optional[int] = None) -> Project:
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
            response = self.session.get_200_or_error(
                url=self.urls.get.format(project_id=pid),
                logger=log,
            )
            data = response.json()
            return Project(**data)
