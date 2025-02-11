import logging
from os import PathLike

from pyodk._endpoints import bases
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class SubmissionAttachment(bases.Model):
    name: str
    exists: bool


class URLs(bases.FrozenModel):
    _submission: str = "projects/{project_id}/forms/{form_id}/submissions/{instance_id}"
    list: str = f"{_submission}/attachments"
    get: str = f"{_submission}/attachments/{{fname}}"
    post: str = f"{_submission}/attachments/{{fname}}"
    delete: str = f"{_submission}/attachments/{{fname}}"


class SubmissionAttachmentService(bases.Service):
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
        instance_id: str | None = None,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> list[SubmissionAttachment]:
        """
        Show all required submission attachments and their upload status.

        :param instance_id: The instanceId of the submission being referenced.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project the Submissions belong to.

        :return: A list of the object representation of all Submission
            attachment metadata.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            iid = pv.validate_form_id(instance_id, self.default_instance_id)
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

    def get(
        self,
        file_name: str,
        instance_id: str,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> bytes:
        """
        Read Submission metadata.

        :param file_name: The file name of the Submission attachment being referenced.
        :param instance_id: The instanceId of the Submission being referenced.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.

        :return: The attachment bytes for download.
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
                self.urls.get,
                project_id=pid,
                form_id=fid,
                instance_id=iid,
                fname=file_name,
            ),
            logger=log,
        )
        return response.content

    def upload(
        self,
        file_path_or_bytes: PathLike | str | bytes,
        instance_id: str,
        file_name: str | None = None,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> bool:
        """
        Upload a Form Draft Attachment.

        :param file_path_or_bytes: The path to the file or file bytes to upload.
        :param instance_id: The instanceId of the Submission being referenced.
        :param file_name: A name for the file, otherwise the name in file_path is used.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            iid = pv.validate_instance_id(instance_id, self.default_instance_id)
            if isinstance(file_path_or_bytes, bytes):
                file_bytes = file_path_or_bytes
                # file_name cannot be empty when passing a bytes object
                pv.validate_str(file_name, key="file_name")
            else:
                file_path = pv.validate_file_path(file_path_or_bytes)
                with open(file_path_or_bytes, "rb") as fd:
                    file_bytes = fd.read()
                if file_name is None:
                    file_name = pv.validate_str(file_path.name, key="file_name")
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

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
            data=file_bytes,
        )
        data = response.json()
        return data["success"]
