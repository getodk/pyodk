import logging
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from pyodk import validators as pv
from pyodk.endpoints import bases
from pyodk.endpoints.submissions import SubmissionService
from pyodk.errors import PyODKError
from pyodk.session import Session

log = logging.getLogger(__name__)


# TODO: actual response has undocumented fields: enketoOnceId, sha, sha256, draftToken


class Form(bases.Model):
    m: "FormManager" = Field(repr=False, exclude=True)

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


class FormManager(bases.Manager):
    __slots__ = ("session", "project_id", "form_id", "_forms", "_submissions")

    def __init__(self, session: Session, project_id: int, form_id: str):
        self.session: Session = session
        self.project_id: int = project_id
        self.form_id: str = form_id
        self._forms: Optional[FormService] = None
        self._submissions: Optional[SubmissionService] = None

    @property
    def forms(self) -> "FormService":
        if self._forms is None:
            self._forms = FormService(
                session=self.session,
                default_project_id=self.project_id,
                default_form_id=self.form_id,
            )
        return self._forms

    @property
    def submissions(self) -> SubmissionService:
        if self._submissions is None:
            self._submissions = SubmissionService(
                session=self.session,
                default_project_id=self.project_id,
                default_form_id=self.form_id,
            )
        return self._submissions

    @classmethod
    def from_dict(
        cls,
        session: Session,
        project_id: int,
        data: Dict,
        form_id: str = None,
    ) -> Form:
        mgr = cls(session=session, project_id=project_id, form_id=form_id)
        return Form(m=mgr, **data)


Form.update_forward_refs()


class URLs(bases.Model):
    class Config:
        frozen = True

    list: str = "projects/{project_id}/forms"
    get: str = "projects/{project_id}/forms/{form_id}"
    get_metadata: str = "projects/{project_id}/forms/{form_id}.svc/$metadata"


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
            return [
                FormManager.from_dict(
                    session=self.session,
                    project_id=pid,
                    form_id=r["xmlFormId"],
                    data=r,
                )
                for r in data
            ]

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
            return FormManager.from_dict(
                session=self.session,
                project_id=pid,
                form_id=data["xmlFormId"],
                data=data,
            )

    def get_metadata(
        self,
        form_id: str,
        project_id: Optional[int] = None,
    ) -> str:
        """
        Read the OData metadata XML.

        :param form_id: The xmlFormId of the Form being referenced.
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
                url=self.urls.get_metadata.format(project_id=pid, form_id=fid),
                logger=log,
            )
            return response.text
