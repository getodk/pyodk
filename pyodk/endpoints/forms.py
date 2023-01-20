import logging
from datetime import datetime
from typing import List, Optional

from pyodk import validators as pv
from pyodk.endpoints import bases
from pyodk.errors import PyODKError
from pyodk.session import Session

log = logging.getLogger(__name__)


# TODO: actual response has undocumented fields: enketoOnceId, sha, sha256, draftToken


class Form(bases.Model):
    projectId: int
    xmlFormId: str
    name: str
    version: str
    enketoId: str
    hash: str
    state: str  # open, closing, closed
    createdAt: datetime
    keyId: Optional[int]
    updatedAt: Optional[datetime]
    publishedAt: Optional[datetime]


class URLs(bases.Model):
    class Config:
        frozen = True

    list: str = "projects/{project_id}/forms"
    get: str = "projects/{project_id}/forms/{form_id}"


class FormService(bases.Service):
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

    def list(self, project_id: Optional[int] = None) -> List[Form]:
        """
        Read the details of all Forms.

        :param project_id: The id of the project the forms belong to.
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
                url=self.urls.list.format(project_id=pid),
                logger=log,
            )
            data = response.json()
            return [Form(**r) for r in data]

    def get(
        self,
        form_id: str,
        project_id: Optional[int] = None,
    ) -> Form:
        """
        Read the details of a Form.

        :param form_id: The id of this form as given in its XForms XML definition.
        :param project_id: The id of the project this form belongs to.
        """
        try:
            pid = pv.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
            fid = pv.validate_form_id(
                form_id=form_id, default_form_id=self.default_form_id
            )
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            response = self.session.get_200_or_error(
                url=self.urls.get.format(project_id=pid, form_id=fid),
                logger=log,
            )
            data = response.json()
            return Form(**data)
