import logging
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional

from pyodk._endpoints import bases
from pyodk._endpoints.form_draft_attachments import FormDraftAttachmentService
from pyodk._endpoints.form_drafts import FormDraftService
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

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
    """
    Form-related functionality is accessed through `client.forms`. For example:

    ```python
    from pyodk.client import Client

    client = Client()
    forms = client.forms.list()
    ```
    """

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

    def _default_kw(self) -> Dict[str, Any]:
        return {
            "default_project_id": self.default_project_id,
            "default_form_id": self.default_form_id,
        }

    def list(self, project_id: Optional[int] = None) -> List[Form]:
        """
        Read all Form details.

        :param project_id: The id of the project the forms belong to.

        :return: A list of object representations of all Forms' metadata.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            response = self.session.response_or_error(
                method="GET",
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
        Read Form details.

        :param form_id: The id of this form as given in its XForms XML definition.
        :param project_id: The id of the project this form belongs to.

        :return: An object representation of the Form's metadata.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            response = self.session.response_or_error(
                method="GET",
                url=self.urls.get.format(project_id=pid, form_id=fid),
                logger=log,
            )
            data = response.json()
            return Form(**data)

    def update(
        self,
        form_id: str,
        project_id: Optional[int] = None,
        definition: Optional[str] = None,
        attachments: Optional[Iterable[str]] = None,
        version_updater: Optional[Callable[[str], str]] = None,
    ) -> None:
        """
        Update an existing Form. Must specify definition, attachments or both.

        Accepted call patterns:
        - definition +/- attachments
        - attachments +/- version_updater

        If a definition is provided, the new version name is presumed to be specified in
        the definition. If no definition is provided, a default version will be set using
        the current datetime is ISO format.

        The default datetime version can be overridden by providing a version_updater
        function. The function will be passed the current version name as a string, and
        must return a string with the new version name. For example the function could
        parse then increment a version number. Or the function could disregard the input
        and return a string e.g. `version_updater=lambda x: "v2.0"`.

        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param definition: The path to a form definition file to upload.
        :param attachments: The paths of the form attachment file(s) to upload.
        :param version_updater: A function that accepts a version name string and returns
          a version name string, which is used for the new form version.
        """
        if definition is None and attachments is None:
            raise PyODKError("Must specify a form definition and/or attachments.")

        if definition is not None and version_updater is not None:
            raise PyODKError("Must not specify both a definition and version_updater.")

        # Start a new draft - with a new definition, if provided.
        fp_ids = {"form_id": form_id, "project_id": project_id}
        fd = FormDraftService(session=self.session, **self._default_kw())
        if not fd.create(file_path=definition, **fp_ids):
            raise PyODKError("Form update (form draft create) failed.")

        # Upload the attachments, if any.
        if attachments is not None:
            fda = FormDraftAttachmentService(session=self.session, **self._default_kw())
            for attach in attachments:
                if not fda.upload(file_path=attach, **fp_ids):
                    raise PyODKError("Form update (attachment upload) failed.")

        new_version = None
        if definition is None:
            # Get a new version - using either a timestamp or the callback.
            if version_updater is None:
                new_version = datetime.now().isoformat()
            else:
                new_version = version_updater(self.get(**fp_ids).version)

        # Publish the draft.
        if not fd.publish(version=new_version, **fp_ids):
            raise PyODKError("Form update (draft publish) failed.")
