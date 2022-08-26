from dataclasses import dataclass, fields
from typing import Dict, List, Optional

from pyodk.errors import PyODKError
from pyodk.session import ClientSession
from pyodk.utils import coalesce

# TODO: convert post-init *At fields from str to datetime e.g. "2018-01-21T00:04:11.153Z"
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
    publishedAt: str
    createdAt: str
    updatedAt: str


class FormService:
    def __init__(self, session: ClientSession, default_project_id: Optional[int] = None):
        self.session: ClientSession = session
        self.default_project_id: Optional[int] = default_project_id

    def _validate_project_id(self, project_id: Optional[int] = None) -> int:
        pid = coalesce(project_id, self.default_project_id)
        if pid is None:
            msg = "No project ID was provided, either directly or via a default setting."
            raise PyODKError(msg)
        return pid

    @staticmethod
    def _validate_form_id(form_id: Optional[str] = None) -> str:
        if form_id is None:
            msg = "No form ID was provided."
            raise PyODKError(msg)
        return form_id

    def _read_all_request(self, project_id: int) -> List[Dict]:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}/forms",
        )
        if response.status_code == 200:
            return response.json()
        else:
            msg = (
                f"The form listing request failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            raise PyODKError(msg)

    def read_all(self, project_id: Optional[int] = None) -> List[FormEntity]:
        """
        Read the details of all Forms.

        :param project_id: The id of the project the forms belong to.
        """
        pid = self._validate_project_id(project_id=project_id)
        raw = self._read_all_request(project_id=pid)
        return [
            FormEntity(**{f.name: r.get(f.name) for f in fields(FormEntity)}) for r in raw
        ]

    def _read_request(self, project_id: int, form_id: str) -> Dict:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}/forms/{form_id}",
        )
        if response.status_code == 200:
            return response.json()
        else:
            msg = (
                f"The form read request failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            raise PyODKError(msg)

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
        pid = self._validate_project_id(project_id=project_id)
        fid = self._validate_form_id(form_id=form_id)
        raw = self._read_request(project_id=pid, form_id=fid)
        return FormEntity(**{f.name: raw.get(f.name) for f in fields(FormEntity)})
