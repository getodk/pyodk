import logging
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from pyodk import validators as pv
from pyodk.endpoints import bases
from pyodk.errors import PyODKError
from pyodk.session import Session

log = logging.getLogger(__name__)


class Submission(bases.Model):
    m: "SubmissionManager" = Field(repr=False, exclude=True)

    instanceId: str
    submitterId: int
    createdAt: datetime
    deviceId: Optional[str]
    # null, edited, hasIssues, rejected, approved
    reviewState: Optional[str]
    userAgent: Optional[str]
    instanceName: Optional[str]
    updatedAt: Optional[datetime]


class SubmissionManager(bases.Manager):
    """An instance of a Submission."""

    __slots__ = ("session", "project_id", "form_id", "_forms", "_submissions")

    def __init__(self, session: Session, project_id: int, form_id: str):
        self.session: Session = session
        self.project_id: int = project_id
        self.form_id: str = form_id
        self._submissions: Optional[SubmissionService] = None

    @property
    def submissions(self) -> "SubmissionService":
        if self._submissions is None:
            self._submissions = SubmissionService(
                session=self.session,
                default_project_id=self.project_id,
                default_form_id=self.form_id,
            )
        return self._submissions

    @classmethod
    def from_dict(
        cls,
        session: Session,
        project_id: int,
        data: Dict,
        form_id: str = None,
    ) -> Submission:
        mgr = cls(session=session, project_id=project_id, form_id=form_id)
        return Submission(m=mgr, **data)


Submission.update_forward_refs()


class URLs(bases.Model):
    class Config:
        frozen = True

    list: str = "projects/{project_id}/forms/{form_id}/submissions"
    get: str = "projects/{project_id}/forms/{form_id}/submissions/{instance_id}"
    get_table: str = "projects/{project_id}/forms/{form_id}.svc/{table_name}"


class SubmissionService(bases.Service):
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

    def list(
        self, form_id: Optional[str] = None, project_id: Optional[int] = None
    ) -> List[Submission]:
        """
        Read the details of all Submissions.

        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project the Submissions belong to.
        """
        try:
            pid = pv.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
            fid = pv.validate_form_id(
                form_id=form_id, default_form_id=self.default_form_id
            )
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            response = self.session.get_200_or_error(
                url=self.urls.list.format(project_id=pid, form_id=fid),
                logger=log,
            )
            data = response.json()
            return [
                SubmissionManager.from_dict(
                    session=self.session,
                    project_id=pid,
                    form_id=fid,
                    data=r,
                )
                for r in data
            ]

    def get(
        self,
        instance_id: str,
        form_id: Optional[str] = None,
        project_id: Optional[int] = None,
    ) -> Submission:
        """
        Read the details of a Submission.

        :param instance_id: The instanceId of the Submission being referenced.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        """
        try:
            pid = pv.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
            fid = pv.validate_form_id(
                form_id=form_id, default_form_id=self.default_form_id
            )
            iid = pv.validate_instance_id(instance_id=instance_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err
        else:
            response = self.session.get_200_or_error(
                url=self.urls.get.format(project_id=pid, form_id=fid, instance_id=iid),
                logger=log,
            )
            data = response.json()
            return SubmissionManager.from_dict(
                session=self.session,
                project_id=pid,
                form_id=fid,
                data=data,
            )

    def get_table(
        self,
        form_id: Optional[str] = None,
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
        Read Submissions as an OData table.

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
            pid = pv.validate_project_id(
                project_id=project_id, default_project_id=self.default_project_id
            )
            fid = pv.validate_form_id(
                form_id=form_id, default_form_id=self.default_form_id
            )
            table = pv.validate_table_name(table_name=table_name)
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
            response = self.session.get_200_or_error(
                url=self.urls.get_table.format(
                    project_id=pid, form_id=fid, table_name=table
                ),
                logger=log,
                params=params,
            )
            return response.json()
