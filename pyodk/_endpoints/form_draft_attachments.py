import logging
from dataclasses import dataclass
from os import PathLike

from pyodk._endpoints.bases import Service
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


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
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        headers = {}
        # Add Content-Type header only for CSV files
        if str(file_path).lower().endswith(".csv"):
            headers["Content-Type"] = "text/csv"

        with open(file_path, "rb") as fd:
            response = self.session.response_or_error(
                method="POST",
                url=self.session.urlformat(
                    self.urls.post, project_id=pid, form_id=fid, fname=file_name
                ),
                logger=log,
                data=fd,
                headers=headers if headers else None,
            )
        data = response.json()
        return data["success"]
