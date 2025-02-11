import logging
from io import BytesIO
from os import PathLike
from zipfile import is_zipfile

from pyodk._endpoints import bases
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)
CONTENT_TYPES = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".xml": "application/xml",
}


def is_xls_file(buf: bytes) -> bool:
    """
    Implements the Microsoft Excel (Office 97-2003) document type matcher.

    From h2non/filetype v1.2.0, MIT License, Copyright (c) 2016 Tomás Aparicio

    :param buf: buffer to match against.
    """
    if len(buf) > 520 and buf[0:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        if buf[512:516] == b"\xfd\xff\xff\xff" and (buf[518] == 0x00 or buf[518] == 0x02):
            return True
        if buf[512:520] == b"\x09\x08\x10\x00\x00\x06\x05\x00":
            return True
        if (
            len(buf) > 2095
            and b"\xe2\x00\x00\x00\x5c\x00\x70\x00\x04\x00\x00Calc" in buf[1568:2095]
        ):
            return True

    return False


def get_definition_data(
    definition: PathLike | str | bytes | None,
) -> (bytes, str, str | None):
    """
    Get the form definition data from a path or bytes.

    :param definition: The path to the file to upload (string or PathLike), or the
          form definition in memory (string (XML) or bytes (XLS/XLSX)).
    :return: definition_data, content_type, file_path_stem (if any).
    """
    definition_data = None
    content_type = None
    file_path_stem = None
    if (
        isinstance(definition, str)
        and """http://www.w3.org/2002/xforms""" in definition[:1000]
    ):
        content_type = CONTENT_TYPES[".xml"]
        definition_data = definition.encode("utf-8")
    elif isinstance(definition, str | PathLike):
        file_path = pv.validate_file_path(definition)
        file_path_stem = file_path.stem
        definition_data = file_path.read_bytes()
        if file_path.suffix not in CONTENT_TYPES:
            raise PyODKError(
                "Parameter 'definition' file name has an unexpected file extension, "
                "expected one of '.xlsx', '.xls', '.xml'."
            )
        content_type = CONTENT_TYPES[file_path.suffix]
    elif isinstance(definition, bytes):
        definition_data = definition
        if is_zipfile(BytesIO(definition)):
            content_type = CONTENT_TYPES[".xlsx"]
        elif is_xls_file(definition):
            content_type = CONTENT_TYPES[".xls"]
    if definition_data is None or content_type is None:
        raise PyODKError(
            "Parameter 'definition' has an unexpected file type, "
            "expected one of '.xlsx', '.xls', '.xml'."
        )
    return definition_data, content_type, file_path_stem


class URLs(bases.FrozenModel):
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
        definition: PathLike | str | bytes | None = None,
        ignore_warnings: bool | None = True,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> (str, str, dict, dict, bytes | None):
        """
        Prepare / validate input arguments for POSTing a new form definition or version.

        :param definition: The path to the file to upload (string or PathLike), or the
          form definition in memory (string (XML) or bytes (XLS/XLSX)).
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param ignore_warnings: If True, create the form if there are XLSForm warnings.
        :return: project_id, form_id, headers, params
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            headers = {}
            params = {}
            definition_data = None
            file_path_stem = None
            if definition is not None:
                definition_data, content_type, file_path_stem = get_definition_data(
                    definition=definition
                )
                headers["Content-Type"] = content_type
            fid = pv.validate_form_id(
                form_id,
                self.default_form_id,
                file_path_stem,
                self.session.get_xform_uuid(),
            )
            if definition is not None:
                if ignore_warnings is not None:
                    key = "ignore_warnings"
                    params["ignoreWarnings"] = pv.validate_bool(ignore_warnings, key=key)
                headers["X-XlsForm-FormId-Fallback"] = self.session.urlquote(fid)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        return pid, fid, headers, params, definition_data

    def create(
        self,
        definition: PathLike | str | bytes | None = None,
        ignore_warnings: bool | None = True,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> bool:
        """
        Create a Form Draft.

        :param definition: The path to the file to upload (string or PathLike), or the
          form definition in memory (string (XML) or bytes (XLS/XLSX)).
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param ignore_warnings: If True, create the form if there are XLSForm warnings.
        """
        pid, fid, headers, params, form_def = self._prep_form_post(
            definition=definition,
            ignore_warnings=ignore_warnings,
            form_id=form_id,
            project_id=project_id,
        )
        response = self.session.response_or_error(
            method="POST",
            url=self.session.urlformat(self.urls.post, project_id=pid, form_id=fid),
            logger=log,
            headers=headers,
            params=params,
            data=form_def,
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
