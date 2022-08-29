import logging
from typing import Dict, List, Optional

from pyodk import validators
from pyodk.errors import PyODKError
from pyodk.session import ClientSession

log = logging.getLogger(__name__)


class ODataService:
    def __init__(self, session: ClientSession, default_project_id: Optional[int] = None):
        self.session: ClientSession = session
        self.default_project_id: Optional[int] = default_project_id

    def _read_table_request(
        self, project_id: int, form_id: str, table_name: str, params: Dict
    ) -> Dict:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}/forms/{form_id}.svc"
            f"/{table_name}",
            params=params,
        )
        if response.status_code == 200:
            return response.json()
        else:
            msg = (
                f"The submission read request failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            err = PyODKError(msg)
            log.error(err, exc_info=True)
            raise err

    # TODO: map filter params to args
    def read_table(
        self,
        form_id: str,
        project_id: Optional[int] = None,
        table_name: Optional[str] = "Submissions",
        params: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Read an OData table.

        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param table_name: The name of the table to be returned.
        :param params: Parameters to pass through to the OData call.
        """
        try:
            pid = validators.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
            fid = validators.validate_form_id(form_id=form_id)
            table = validators.validate_table_name(table_name=table_name)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            raw = self._read_table_request(
                project_id=pid, form_id=fid, table_name=table, params=params
            )
            return raw["value"]
