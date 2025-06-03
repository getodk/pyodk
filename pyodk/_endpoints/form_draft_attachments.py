import logging
import mimetypes
from dataclasses import dataclass
from datetime import datetime
from os import PathLike

from pyodk._endpoints.bases import Model, Service
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class FormAttachment(Model):
    name: str
    type: str  # image | audio | video | file
    hash: str
    exists: bool  # Either blobExists or dataExists is True
    blobExists: bool  # Server has the file
    datasetExists: bool  # File is linked to a Dataset
    updatedAt: datetime  # When the file was created or deleted


@dataclass(frozen=True, slots=True)
class URLs:
    _form: str = "projects/{project_id}/forms/{form_id}"
    post: str = f"{_form}/draft/attachments/{{fname}}"


class FormDraftAttachmentService(Service):
    __slots__ = ("urls", "session", "default_project_id", "default_form_id")

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

    def upload(
        self,
        file_path: PathLike | str,
        file_name: str | None = None,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> bool:
        """
        Upload a Form Draft Attachment.

        :param file_path: The path to the file to upload.
        :param file_name: A name for the file, otherwise the name in file_path is used.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            file_path = pv.validate_file_path(file_path)
            if file_name is None:
                file_name = pv.validate_str(file_path.name, key="file_name")
            guess_type, guess_encoding = mimetypes.guess_type(file_name)
            headers = {
                "Transfer-Encoding": "chunked",
                "Content-Type": guess_type or "application/octet-stream",
            }
            if guess_encoding:  # associated compression type, if any.
                headers["Content-Encoding"] = guess_encoding
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        def file_stream():
            # Generator forces requests to read/send in chunks instead of all at once.
            with open(file_path, "rb") as f:
                while chunk := f.read(self.session.blocksize):
                    yield chunk

        response = self.session.response_or_error(
            method="POST",
            url=self.session.urlformat(
                self.urls.post,
                project_id=pid,
                form_id=fid,
                fname=file_name,
            ),
            logger=log,
            headers=headers,
            data=file_stream(),
        )
        data = response.json()
        try:
            # Response format prior to Central v2025.1 is constant `{"success": True}`.
            return data["success"]
        except KeyError:
            # Response introduced in Central v2025.1. Model details currently not used.
            return FormAttachment(**data).exists
