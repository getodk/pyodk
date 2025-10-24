import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from os import PathLike
from typing import Any

from pyodk._endpoints.bases import Model, Service
from pyodk._endpoints.form_draft_attachments import FormDraftAttachmentService
from pyodk._endpoints.form_drafts import FormDraftService
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


# TODO: actual response has undocumented fields: enketoOnceId, sha, sha256, draftToken


class Form(Model):
    projectId: int
    xmlFormId: str
    version: str
    hash: str
    state: str  # open, closing, closed
    createdAt: datetime
    name: str | None  # Null if Central couldn't parse the XForm title, or it was blank.
    enketoId: str | None  # Null if Enketo not being used with Central.
    keyId: int | None
    updatedAt: datetime | None
    publishedAt: datetime | None


@dataclass(frozen=True, slots=True)
class URLs:
    forms: str = "projects/{project_id}/forms"
    get: str = f"{forms}/{{form_id}}"
    get_xml: str = f"{forms}/{{form_id}}.xml"


class FormService(Service):
    """
    Form-related functionality is accessed through `client.forms`. For example:

    ```python
    from pyodk.client import Client

    client = Client()
    forms = client.forms.list()
    ```
    """

    __slots__ = ("default_form_id", "default_project_id", "session", "urls")

    def __init__(
        self,
        session: Session,
        default_project_id: int | None = None,
        default_form_id: str | None = None,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session
        self.default_project_id: int | None = default_project_id
        self.default_form_id: str | None = default_form_id

    def _default_kw(self) -> dict[str, Any]:
        return {
            "default_project_id": self.default_project_id,
            "default_form_id": self.default_form_id,
        }

    def list(self, project_id: int | None = None) -> list[Form]:
        """
        Read all Form details.

        :param project_id: The id of the project the forms belong to.

        :return: A list of object representations of all Forms' metadata.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise
        else:
            response = self.session.response_or_error(
                method="GET",
                url=self.session.urlformat(self.urls.forms, project_id=pid),
                logger=log,
            )
            data = response.json()
            return [Form(**r) for r in data]

    def get(
        self,
        form_id: str,
        project_id: int | None = None,
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
            raise
        else:
            response = self.session.response_or_error(
                method="GET",
                url=self.session.urlformat(self.urls.get, project_id=pid, form_id=fid),
                logger=log,
            )
            data = response.json()
            return Form(**data)

    def get_xml(
        self,
        form_id: str,
        project_id: int | None = None,
        encoding: str | None = "utf-8",
    ) -> str | bytes:
        """
        Read the form XForms XML document.

        :param form_id: The id of this form as given in its XForms XML definition.
        :param project_id: The id of the project this form belongs to.
        :param encoding: The string encoding of the XML document. If "bytes" then the
          document will be returned as bytes, otherwise the encoding parameter value will
          be used to decode the bytes to return a string.

        :return: The XForms XML document.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="GET",
            url=self.session.urlformat(self.urls.get_xml, project_id=pid, form_id=fid),
            logger=log,
        )
        if encoding:
            return response.content.decode(encoding)
        else:
            return response.content

    def create(
        self,
        definition: PathLike | str | bytes,
        attachments: Iterable[PathLike | str] | None = None,
        ignore_warnings: bool | None = True,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> Form:
        """
        Create a form.

        :param definition: The path to the file to upload (string or PathLike), or the
          form definition in memory (string (XML) or bytes (XLS/XLSX)).
        :param attachments: The paths of the form attachment file(s) to upload.
        :param ignore_warnings: If True, create the form if there are XLSForm warnings.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :return: An object representation of the Form's metadata.
        """
        fd = FormDraftService(session=self.session, **self._default_kw())
        pid, fid, headers, params, form_def = fd._prep_form_post(
            definition=definition,
            ignore_warnings=ignore_warnings,
            form_id=form_id,
            project_id=project_id,
        )

        # Create the new Form definition, in draft state.
        params["publish"] = False
        response = self.session.response_or_error(
            method="POST",
            url=self.session.urlformat(self.urls.forms, project_id=pid),
            logger=log,
            headers=headers,
            params=params,
            data=form_def,
        )
        data = response.json()

        # In case the form_id parameter was None, use the (maybe generated) response value.
        form = Form(**data)
        fp_ids = {"form_id": form.xmlFormId, "project_id": project_id}

        # Upload the attachments, if any.
        if attachments is not None:
            fda = FormDraftAttachmentService(session=self.session, **self._default_kw())
            for attach in attachments:
                if not fda.upload(file_path=attach, **fp_ids):
                    raise PyODKError("Form create (attachment upload) failed.")

        # Publish the draft.
        if not fd.publish(**fp_ids):
            raise PyODKError("Form create (draft publish) failed.")

        return form

    def update(
        self,
        form_id: str,
        project_id: int | None = None,
        definition: PathLike | str | bytes | None = None,
        attachments: Iterable[PathLike | str] | None = None,
        version_updater: Callable[[str], str] | None = None,
    ) -> None:
        """
        Update an existing Form. Must specify definition, attachments or both.

        Accepted call patterns:

        * form definition only
        * form definition with attachments
        * form attachments only
        * form attachments with `version_updater`

        If a definition is provided, the new version name must be specified in the
        definition. If no definition is provided, a default version will be set using
        the current datetime is ISO format.

        The default datetime version can be overridden by providing a `version_updater`
        function. The function will be passed the current version name as a string, and
        must return a string with the new version name. For example:

        * Parse then increment a version number: `version_updater=lambda v: int(v) + 1`
        * Disregard the input and return a string: `version_updater=lambda v: "v2.0"`.

        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param definition: The path to the file to upload (string or PathLike), or the
          form definition in memory (string (XML) or bytes (XLS/XLSX)). The form
          definition must include an updated version string.
        :param attachments: The paths of the form attachment file(s) to upload.
        :param version_updater: A function that accepts a version name string and returns
          a version name string, which is used for the new form version. Not allowed if a
          form definition is specified.
        """
        if definition is None and attachments is None:
            raise PyODKError("Must specify a form definition and/or attachments.")

        if definition is not None and version_updater is not None:
            raise PyODKError("Must not specify both a definition and version_updater.")

        # Start a new draft - with a new definition, if provided.
        fp_ids = {"form_id": form_id, "project_id": project_id}
        fd = FormDraftService(session=self.session, **self._default_kw())
        if not fd.create(definition=definition, **fp_ids):
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
