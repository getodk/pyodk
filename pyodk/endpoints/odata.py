import logging
from typing import Dict, Optional

from pyodk import validators
from pyodk.endpoints.utils import error_if_not_200
from pyodk.errors import PyODKError
from pyodk.session import ClientSession

log = logging.getLogger(__name__)


class ODataService:
    def __init__(self, session: ClientSession, default_project_id: Optional[int] = None):
        self.session: ClientSession = session
        self.default_project_id: Optional[int] = default_project_id

    def _read_metadata_request(self, project_id: int, form_id: str) -> str:
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

    def read_metadata(
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
            return self._read_metadata_request(
                project_id=pid,
                form_id=fid,
            )

    def _read_table_request(
        self, project_id: int, form_id: str, table_name: str, params: Dict
    ) -> Dict:
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/projects/{project_id}/forms/{form_id}.svc"
            f"/{table_name}",
            params=params,
        )
        return error_if_not_200(response=response, log=log, action="table read")

    def read_table(
        self,
        form_id: str,
        project_id: Optional[int] = None,
        table_name: Optional[str] = "Submissions",
        skip: Optional[int] = None,
        top: Optional[int] = None,
        count: Optional[bool] = None,
        wkt: Optional[bool] = None,
        filter: Optional[str] = None,
        expand: Optional[str] = None,
    ) -> Dict:
        """
        Read an OData table.

        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param table_name: The name of the table to be returned.
        :param skip: The first n rows will be omitted from the results.
        :param top: Only up to n rows will be returned in the results.
        :param count: If True, an @odata.count property will be added to the result to
          indicate the total number of rows, ignoring the above paging parameters.
        :param wkt: If True, geospatial data will be returned as Well-Known Text (WKT)
          strings rather than GeoJSON structures.
        :param filter: Filter responses to those matching the query. Only certain fields
          are available to reference (submitterId, createdAt, updatedAt, reviewState).
          The operators lt, le, eq, neq, ge, gt, not, and, and or are supported, and the
          built-in functions now, year, month, day, hour, minute, second.
        :param expand: Repetitions, which should get expanded. Currently, only `*` (star)
          is implemented, which expands all repetitions.
        """
        try:
            pid = validators.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
            fid = validators.validate_form_id(form_id=form_id)
            table = validators.validate_table_name(table_name=table_name)
            params = {
                k: v
                for k, v in {
                    "$skip": skip,
                    "$top": top,
                    "$count": count,
                    "$wkt": wkt,
                    "$filter": filter,
                    "$expand": expand,
                }.items()
                if v is not None
            }
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            return self._read_table_request(
                project_id=pid,
                form_id=fid,
                table_name=table,
                params=params,
            )
