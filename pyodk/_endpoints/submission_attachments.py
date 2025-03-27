import logging
import mimetypes
from dataclasses import dataclass
from os import PathLike

from pyodk._endpoints.bases import Model, Service
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class SubmissionAttachment(Model):
    name: str
    exists: bool


@dataclass(frozen=True, slots=True)
class URLs:
    _submission: str = "projects/{project_id}/forms/{form_id}/submissions/{instance_id}"
    list: str = f"{_submission}/attachments"
    post: str = f"{_submission}/attachments/{{fname}}"


class SubmissionAttachmentService(Service):
    __slots__ = (
        "urls",
        "session",
        "default_project_id",
        "default_form_id",
        "default_instance_id",
    )

    def __init__(
        self,
        session: Session,
        default_project_id: int | None = None,
        default_form_id: str | None = None,
        default_instance_id: str | None = None,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session
        self.default_project_id: int | None = default_project_id
        self.default_form_id: str | None = default_form_id
        self.default_instance_id: str | None = default_instance_id

    def list(
        self,
        form_id: str | None = None,
        project_id: int | None = None,
        instance_id: str | None = None,
    ) -> list[SubmissionAttachment]:
        """
        Read all Submission Attachment details.

        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project the Submissions belong to.
        :param instance_id: The instanceId of the Submission being referenced.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            iid = pv.validate_instance_id(instance_id, self.default_instance_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="GET",
            url=self.session.urlformat(
                self.urls.list, project_id=pid, form_id=fid, instance_id=iid
            ),
            logger=log,
        )
        data = response.json()
        return [SubmissionAttachment(**r) for r in data]

    def upload(
        self,
        file_path: PathLike | str,
        file_name: str | None = None,
        project_id: int | None = None,
        form_id: str | None = None,
        instance_id: str | None = None,
    ) -> bool:
        """
        Upload a Submission Attachment.

        :param file_path: The path to the file to upload.
        :param file_name: A name for the file, otherwise the name in file_path is used.
        :param project_id: The id of the project this form belongs to.
        :param form_id: The xmlFormId of the Form being referenced.
        :param instance_id: The instanceId of the Submission being referenced.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            iid = pv.validate_instance_id(instance_id, self.default_instance_id)
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
                instance_id=iid,
                fname=file_name,
            ),
            logger=log,
            headers=headers,
            data=file_stream(),
        )
        data = response.json()
        return data["success"]
