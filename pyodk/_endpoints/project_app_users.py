import logging
from datetime import datetime
from typing import List, Optional

from pyodk._endpoints import bases
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class ProjectAppUser(bases.Model):
    projectId: int
    id: int
    displayName: str
    createdAt: datetime
    type: Optional[str]  # user, field_key, public_link, singleUse
    token: Optional[str]
    updatedAt: Optional[datetime]
    deletedAt: Optional[datetime]


class URLs(bases.Model):
    class Config:
        frozen = True

    list: str = "projects/{project_id}/app-users"
    post: str = "projects/{project_id}/app-users"


class ProjectAppUserService(bases.Service):
    __slots__ = (
        "urls",
        "session",
        "default_project_id",
    )

    def __init__(
        self,
        session: Session,
        default_project_id: Optional[int] = None,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session
        self.default_project_id: Optional[int] = default_project_id

    def list(
        self,
        project_id: Optional[int] = None,
    ) -> List[ProjectAppUser]:
        """
        Read all ProjectAppUser details.

        :param project_id: The project_id the ProjectAppUsers are assigned to.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err

        response = self.session.response_or_error(
            method="GET",
            url=self.urls.list.format(project_id=pid),
            logger=log,
        )
        data = response.json()
        return [ProjectAppUser(**r) for r in data]

    def create(
        self,
        display_name: str,
        project_id: Optional[int] = None,
    ) -> ProjectAppUser:
        """
        Create a ProjectAppUser.

        :param display_name: The friendly nickname of the App User to be created.
        :param project_id: The project_id the ProjectAppUser should be assigned to.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            display_name = pv.wrap_error(
                validator=pv.v.str_validator, key="display_name", value=display_name
            )
            json = {"displayName": display_name}
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err

        response = self.session.response_or_error(
            method="POST",
            url=self.urls.post.format(project_id=pid),
            logger=log,
            json=json,
        )
        data = response.json()
        return ProjectAppUser(**data)
