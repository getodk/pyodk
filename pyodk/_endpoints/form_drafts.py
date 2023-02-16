import logging
from contextlib import nullcontext
from pathlib import Path
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
    post: str = f"{_form}/draft"
    post_publish: str = f"{_form}/draft/publish"


class FormDraftService(bases.Service):
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

    def create(
        self,
        file_path: Optional[str] = None,
        ignore_warnings: Optional[bool] = True,
        form_id: Optional[str] = None,
        project_id: Optional[int] = None,
    ) -> bool:
        """
        Create a Form Draft.

        :param file_path: The path to the file to upload.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param ignore_warnings: If True, create the form if there are XLSForm warnings.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            headers = {}
            params = {}
            if file_path is not None:
                if ignore_warnings is not None:
                    key = "ignore_warnings"
                    params["ignoreWarnings"] = pv.validate_bool(ignore_warnings, key=key)
                file_path = Path(pv.validate_file_path(file_path))
                if file_path.suffix == ".xlsx":
                    content_type = (
                        "application/vnd.openxmlformats-"
                        "officedocument.spreadsheetml.sheet"
                    )
                elif file_path.suffix == ".xls":
                    content_type = "application/vnd.ms-excel"
                elif file_path.suffix == ".xml":
                    content_type = "application/xml"
                else:
                    raise PyODKError(
                        "Parameter 'file_path' file name has an unexpected extension, "
                        "expected one of '.xlsx', '.xls', '.xml'."
                    )
                headers = {
                    "Content-Type": content_type,
                    "X-XlsForm-FormId-Fallback": file_path.stem,
                }
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err

        with open(file_path, "rb") if file_path is not None else nullcontext() as fd:
            response = self.session.response_or_error(
                method="POST",
                url=self.urls.post.format(project_id=pid, form_id=fid),
                logger=log,
                headers=headers,
                params=params,
                data=fd,
            )

        data = response.json()
        return data["success"]

    def publish(
        self,
        form_id: Optional[str] = None,
        project_id: Optional[int] = None,
        version: Optional[str] = None,
    ) -> bool:
        """
        Publish a Form Draft.

        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param version: The version to be associated with the Draft once it's published.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            params = {}
            if version is not None:
                key = "version"
                params[key] = pv.validate_str(version, key=key)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err

        response = self.session.response_or_error(
            method="POST",
            url=self.urls.post_publish.format(project_id=pid, form_id=fid),
            logger=log,
            params=params,
        )
        data = response.json()
        return data["success"]
