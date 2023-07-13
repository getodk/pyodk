import logging
from typing import Optional

from pyodk._endpoints import bases
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class URLs(bases.Model):
    class Config:
        frozen = True

    _form: str = "projects/{project_id}/forms/{form_id}"
    post: str = f"{_form}/assignments/{{role_id}}/{{user_id}}"


class FormAssignmentService(bases.Service):
    __slots__ = ("urls", "session", "default_project_id", "default_form_id")

    def __init__(
        self,
        session: Session,
        default_project_id: Optional[int] = None,
        default_form_id: Optional[str] = None,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session
        self.default_project_id: Optional[int] = default_project_id
        self.default_form_id: Optional[str] = default_form_id

    def assign(
        self,
        role_id: int,
        user_id: int,
        form_id: Optional[str] = None,
        project_id: Optional[int] = None,
    ) -> bool:
        """
        Assign a user to a role for a form.

        :param role_id: The id of the role to assign the user to.
        :param user_id: The id of the user to assign to the role.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            rid = pv.validate_int(role_id, key="role_id")
            uid = pv.validate_int(user_id, key="user_id")
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err

        response = self.session.response_or_error(
            method="POST",
            url=self.session.urlformat(
                self.urls.post, project_id=pid, form_id=fid, role_id=rid, user_id=uid
            ),
            logger=log,
        )

        data = response.json()
        return data["success"]
