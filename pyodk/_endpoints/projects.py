import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from pyodk._endpoints import bases
from pyodk._endpoints.form_assignments import FormAssignmentService
from pyodk._endpoints.project_app_users import ProjectAppUser, ProjectAppUserService
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class Project(bases.Model):
    id: int
    name: str
    createdAt: datetime
    description: Optional[str] = None
    archived: Optional[bool] = None
    keyId: Optional[int] = None
    appUsers: Optional[int] = None
    forms: Optional[int] = None
    lastSubmission: Optional[str] = None
    updatedAt: Optional[datetime] = None
    deletedAt: Optional[datetime] = None


class URLs(bases.Model):
    class Config:
        frozen = True

    list: str = "projects"
    get: str = "projects/{project_id}"
    get_data: str = "projects/{project_id}/forms/{form_id}.svc/{table_name}"
    post_app_users: str = "projects/{project_id}/app-users"


class ProjectService(bases.Service):
    """
    Project-related functionality is accessed through `client.projects`. For example:

    ```python
    from pyodk.client import Client

    client = Client()
    projects = client.projects.list()
    ```
    """

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

    def _default_kw(self) -> Dict[str, Any]:
        return {
            "default_project_id": self.default_project_id,
        }

    def list(self) -> List[Project]:
        """
        Read Project details.

        :return: An list of object representations of the Projects' metadata.
        """
        response = self.session.response_or_error(
            method="GET",
            url=self.urls.list,
            logger=log,
        )
        data = response.json()
        return [Project(**r) for r in data]

    def get(self, project_id: Optional[int] = None) -> Project:
        """
        Read all Project details.

        :param project_id: The id of the project to read.

        :return: An object representation of the Project's metadata.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            response = self.session.response_or_error(
                method="GET",
                url=self.session.urlformat(self.urls.get, project_id=pid),
                logger=log,
            )
            data = response.json()
            return Project(**data)

    def create_app_users(
        self,
        display_names: Iterable[str],
        forms: Optional[Iterable[str]] = None,
        project_id: Optional[int] = None,
    ) -> List[ProjectAppUser]:
        """
        Create new project app users and optionally assign forms to them.

        :param display_names: The friendly nicknames of the app users to be created.
        :param forms: The xmlFormIds of the forms to assign the app users to.
        :param project_id: The id of the project this form belongs to.
        """
        if display_names is None:
            raise PyODKError("Must specify display_names.")

        pid = {"project_id": project_id}
        pau = ProjectAppUserService(session=self.session, **self._default_kw())
        fa = FormAssignmentService(session=self.session, **self._default_kw())

        current = set(u.displayName for u in pau.list(**pid) if u.token is not None)
        to_create = (user for user in display_names if user not in current)
        users = [pau.create(display_name=n, **pid) for n in to_create]
        # The "App User" role_id should always be "2", so no need to look it up by name.
        # Ref: "https://github.com/getodk/central-backend/blob/9db0d792cf4640ec7329722984
        #   cebdee3687e479/lib/model/migrations/20181212-01-add-roles.js"
        # See also roles data in `tests/resorces/projects_data.py`.
        if forms is not None:
            for user in users:
                for form_id in forms:
                    if not fa.assign(role_id=2, user_id=user.id, form_id=form_id, **pid):
                        raise PyODKError("Role assignment failed.")

        return users
