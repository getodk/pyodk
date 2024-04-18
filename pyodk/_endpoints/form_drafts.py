import logging
from contextlib import nullcontext
from pathlib import Path

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
        default_project_id: int | None = None,
        default_form_id: str | None = None,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session
        self.default_project_id: int | None = default_project_id
        self.default_form_id: str | None = default_form_id

    def _prep_form_post(
        self,
        file_path: Path | str | None = None,
        ignore_warnings: bool | None = True,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> (str, str, dict, dict):
        """
        Prepare / validate input arguments for POSTing a new form definition or version.

        :param file_path: The path to the file to upload.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param ignore_warnings: If True, create the form if there are XLSForm warnings.
        :return: project_id, form_id, headers, params
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            headers = {}
            params = {}
            file_path_stem = None
            if file_path is not None:
                file_path = Path(pv.validate_file_path(file_path))
                file_path_stem = file_path.stem
            fid = pv.validate_form_id(
                form_id,
                self.default_form_id,
                file_path_stem,
                self.session.get_xform_uuid(),
            )
            if file_path is not None:
                if ignore_warnings is not None:
                    key = "ignore_warnings"
                    params["ignoreWarnings"] = pv.validate_bool(ignore_warnings, key=key)
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
                    raise PyODKError(  # noqa: TRY301
                        "Parameter 'file_path' file name has an unexpected extension, "
                        "expected one of '.xlsx', '.xls', '.xml'."
                    )
                headers = {
                    "Content-Type": content_type,
                    "X-XlsForm-FormId-Fallback": self.session.urlquote(fid),
                }
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        return pid, fid, headers, params

    def create(
        self,
        file_path: Path | str | None = None,
        ignore_warnings: bool | None = True,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> bool:
        """
        Create a Form Draft.

        :param file_path: The path to the file to upload.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param ignore_warnings: If True, create the form if there are XLSForm warnings.
        """
        pid, fid, headers, params = self._prep_form_post(
            file_path=file_path,
            ignore_warnings=ignore_warnings,
            form_id=form_id,
            project_id=project_id,
        )

        with open(file_path, "rb") if file_path is not None else nullcontext() as fd:
            response = self.session.response_or_error(
                method="POST",
                url=self.session.urlformat(self.urls.post, project_id=pid, form_id=fid),
                logger=log,
                headers=headers,
                params=params,
                data=fd,
            )

        data = response.json()
        return data["success"]

    def publish(
        self,
        form_id: str | None = None,
        project_id: int | None = None,
        version: str | None = None,
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
            raise

        response = self.session.response_or_error(
            method="POST",
            url=self.session.urlformat(
                self.urls.post_publish, project_id=pid, form_id=fid
            ),
            logger=log,
            params=params,
        )
        data = response.json()
        return data["success"]
