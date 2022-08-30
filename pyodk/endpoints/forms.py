import logging
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Dict, List, Optional

from pyodk import validators
from pyodk.endpoints.utils import error_if_not_200
from pyodk.errors import PyODKError
from pyodk.session import ClientSession
from pyodk.utils import STRPTIME_FMT_UTC

log = logging.getLogger(__name__)


# TODO: actual response has undocumented fields: enketoOnceId, sha, sha256, draftToken


@dataclass
class FormEntity:

    projectId: int
    xmlFormId: str
    name: str
    version: str
    enketoId: str
    hash: str
    keyId: int
    state: str  # open, closing, closed
    createdAt: str
    updatedAt: Optional[datetime] = None
    publishedAt: Optional[datetime] = None

    def __post_init__(self):
        # Convert date strings to datetime objects.
        dt_fields = ["createdAt", "updatedAt", "publishedAt"]
        for d in dt_fields:
            dt_value = getattr(self, d)
            if isinstance(dt_value, str):
                setattr(self, d, datetime.strptime(dt_value, STRPTIME_FMT_UTC))


class FormService:
    def __init__(self, session: ClientSession, default_project_id: Optional[int] = None):
        self.session: ClientSession = session
        self.default_project_id: Optional[int] = default_project_id

    def _read_all_request(self, project_id: int) -> List[Dict]:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}/forms",
        )
        return error_if_not_200(response=response, log=log, action="form listing")

    def read_all(self, project_id: Optional[int] = None) -> List[FormEntity]:
        """
        Read the details of all Forms.

        :param project_id: The id of the project the forms belong to.
        """
        try:
            pid = validators.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            raw = self._read_all_request(project_id=pid)
            return [
                FormEntity(**{f.name: r.get(f.name) for f in fields(FormEntity)})
                for r in raw
            ]

    def _read_request(self, project_id: int, form_id: str) -> Dict:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}/forms/{form_id}",
        )
        return error_if_not_200(response=response, log=log, action="form read")

    def read(
        self,
        form_id: str,
        project_id: Optional[int] = None,
    ) -> FormEntity:
        """
        Read the details of a Form.

        :param form_id: The id of this form as given in its XForms XML definition.
        :param project_id: The id of the project this form belongs to.
        """
        try:
            pid = validators.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
            fid = validators.validate_form_id(form_id=form_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            raw = self._read_request(project_id=pid, form_id=fid)
            return FormEntity(**{f.name: raw.get(f.name) for f in fields(FormEntity)})

    def _read_odata_metadata_request(self, project_id: int, form_id: str) -> str:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}/forms/{form_id}.svc"
            f"/$metadata",
        )
        if response.status_code == 200:
            return response.text
        else:
            msg = (
                f"The metadata read request failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            err = PyODKError(msg)
            log.error(err, exc_info=True)
            raise err

    def read_odata_metadata(
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
            pid = validators.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
            fid = validators.validate_form_id(form_id=form_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            return self._read_odata_metadata_request(
                project_id=pid,
                form_id=fid,
            )
