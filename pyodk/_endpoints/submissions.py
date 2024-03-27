import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from pyodk._endpoints import bases
from pyodk._endpoints.comments import Comment, CommentService
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class Submission(bases.Model):
    instanceId: str
    submitterId: int
    createdAt: datetime
    deviceId: str | None = None
    # null, edited, hasIssues, rejected, approved
    reviewState: str | None = None
    userAgent: str | None = None
    instanceName: str | None = None
    updatedAt: datetime | None = None


class URLs(bases.Model):
    class Config:
        frozen = True

    _form: str = "projects/{project_id}/forms/{form_id}"
    list: str = f"{_form}/submissions"
    get: str = f"{_form}/submissions/{{instance_id}}"
    get_table: str = f"{_form}.svc/{{table_name}}"
    post: str = f"{_form}/submissions"
    patch: str = f"{_form}/submissions/{{instance_id}}"
    put: str = f"{_form}/submissions/{{instance_id}}"


class SubmissionService(bases.Service):
    """
    Submission-related functionality is accessed through `client.submissions`. For example:

    ```python
    from pyodk.client import Client

    client = Client()
    data = client.submissions.get_table(form_id="my-form")["value"]
    ```
    """

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

    def _default_kw(self) -> dict[str, Any]:
        return {
            "default_project_id": self.default_project_id,
            "default_form_id": self.default_form_id,
        }

    def list(
        self, form_id: str | None = None, project_id: int | None = None
    ) -> list[Submission]:
        """
        Read all Submission metadata.

        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project the Submissions belong to.

        :return: A list of the object representation of all Submissions' metadata.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="GET",
            url=self.session.urlformat(self.urls.list, project_id=pid, form_id=fid),
            logger=log,
        )
        data = response.json()
        return [Submission(**r) for r in data]

    def get(
        self,
        instance_id: str,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> Submission:
        """
        Read Submission metadata.

        :param instance_id: The instanceId of the Submission being referenced.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.

        :return: An object representation of the Submission's metadata.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            iid = pv.validate_instance_id(instance_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="GET",
            url=self.session.urlformat(
                self.urls.get, project_id=pid, form_id=fid, instance_id=iid
            ),
            logger=log,
        )
        data = response.json()
        return Submission(**data)

    def get_table(
        self,
        form_id: str | None = None,
        project_id: int | None = None,
        table_name: str | None = "Submissions",
        skip: int | None = None,
        top: int | None = None,
        count: bool | None = None,
        wkt: bool | None = None,
        filter: str | None = None,
        expand: str | None = None,
    ) -> dict:
        """
        Read Submission data.

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

        :return: A dictionary representation of the OData JSON document.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            table = pv.validate_table_name(table_name)
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
            raise

        response = self.session.response_or_error(
            method="GET",
            url=self.session.urlformat(
                self.urls.get_table, project_id=pid, form_id=fid, table_name=table
            ),
            logger=log,
            params=params,
        )
        return response.json()

    def create(
        self,
        xml: str,
        form_id: str | None = None,
        project_id: int | None = None,
        device_id: str | None = None,
        encoding: str = "utf-8",
    ) -> Submission:
        """
        Create a Submission.

        Example submission XML structure:

        ```
        <data id="my_form" version="v1">
          <meta>
            <instanceID>uuid:85cb9aff-005e-4edd-9739-dc9c1a829c44</instanceID>
          </meta>
          <name>Alice</name>
          <age>36</age>
        </data>
        ```

        :param xml: The submission XML.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param device_id: An optional deviceID associated with the submission.
        :param encoding: The encoding of the submission XML, default "utf-8".
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            params = {}
            if device_id is not None:
                params["deviceID"] = pv.validate_str(device_id, key="device_id")
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="POST",
            url=self.session.urlformat(self.urls.post, project_id=pid, form_id=fid),
            logger=log,
            headers={"Content-Type": "application/xml"},
            params=params,
            data=xml.encode(encoding=encoding),
        )
        data = response.json()
        return Submission(**data)

    def _put(
        self,
        instance_id: str,
        xml: str,
        form_id: str | None = None,
        project_id: int | None = None,
        encoding: str = "utf-8",
    ) -> Submission:
        """
        Update Submission data.

        :param instance_id: The instanceId of the Submission being referenced.
        :param xml: The submission XML.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param encoding: The encoding of the submission XML, default "utf-8".
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            iid = pv.validate_instance_id(instance_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="PUT",
            url=self.session.urlformat(
                self.urls.put, project_id=pid, form_id=fid, instance_id=iid
            ),
            logger=log,
            headers={"Content-Type": "application/xml"},
            data=xml.encode(encoding=encoding),
        )
        data = response.json()
        return Submission(**data)

    def _patch(
        self,
        instance_id: str,
        review_state: str,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> Submission:
        """
        Update Submission metadata.

        :param instance_id: The instanceId of the Submission being referenced.
        :param review_state: The current review state of the submission.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            iid = pv.validate_instance_id(instance_id)
            json = {}
            if review_state is not None:
                json["reviewState"] = review_state
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="PATCH",
            url=self.session.urlformat(
                self.urls.patch, project_id=pid, form_id=fid, instance_id=iid
            ),
            logger=log,
            json=json,
        )
        data = response.json()
        return Submission(**data)

    def edit(
        self,
        instance_id: str,
        xml: str,
        form_id: str | None = None,
        project_id: int | None = None,
        comment: str | None = None,
        encoding: str = "utf-8",
    ) -> None:
        """
        Edit a submission and optionally comment on it.

        Example edited submission XML structure:

        ```
        <data id="my_form" version="v1">
          <meta>
            <deprecatedID>uuid:85cb9aff-005e-4edd-9739-dc9c1a829c44</deprecatedID>
            <instanceID>uuid:315c2f74-c8fc-4606-ae3f-22f8983e441e</instanceID>
          </meta>
          <name>Alice</name>
          <age>36</age>
        </data>
        ```

        :param instance_id: The instanceId of the Submission being referenced. The
          `instance_id` each Submission is first submitted with will always represent
          that Submission as a whole. Each version of the Submission, though, has its own
          `instance_id`. So `instance_id` will not necessarily match the values in
           the XML elements named `instanceID` and `deprecatedID`.
        :param xml: The submission XML.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param comment: The text of the comment.
        :param encoding: The encoding of the submission XML, default "utf-8".
        """
        fp_ids = {"form_id": form_id, "project_id": project_id}
        self._put(instance_id=instance_id, xml=xml, encoding=encoding, **fp_ids)
        if comment is not None:
            self.add_comment(instance_id=instance_id, comment=comment, **fp_ids)

    def review(
        self,
        instance_id: str,
        review_state: str,
        form_id: str | None = None,
        project_id: int | None = None,
        comment: str | None = None,
    ) -> None:
        """
        Update Submission metadata and optionally comment on it.

        :param instance_id: The instanceId of the Submission being referenced.
        :param review_state: The current review state of the submission.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project this form belongs to.
        :param comment: The text of the comment.
        """
        fp_ids = {"form_id": form_id, "project_id": project_id}
        self._patch(instance_id=instance_id, review_state=review_state, **fp_ids)
        if comment is not None:
            self.add_comment(instance_id=instance_id, comment=comment, **fp_ids)

    def list_comments(
        self,
        instance_id: str,
        form_id: str | None = None,
        project_id: int | None = None,
    ) -> Iterable[Comment]:
        """
        Read all Comment details.

        :param instance_id: The instanceId of the Submission being referenced.
        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project the Submissions belong to.

        :return: A list of all Comments.
        """
        fp_ids = {"form_id": form_id, "project_id": project_id}
        comment_svc = CommentService(session=self.session, **self._default_kw())
        return comment_svc.list(instance_id=instance_id, **fp_ids)

    def add_comment(
        self,
        instance_id: str,
        comment: str,
        project_id: int | None = None,
        form_id: str | None = None,
    ) -> Comment:
        """
        Create a Comment.

        :param instance_id: The instanceId of the Submission being referenced.
        :param comment: The text of the comment.
        :param project_id: The id of the project this form belongs to.
        :param form_id: The xmlFormId of the Form being referenced.

        :return: An object representation of the newly-created Comment.
        """
        fp_ids = {"form_id": form_id, "project_id": project_id}
        comment_svc = CommentService(session=self.session, **self._default_kw())
        return comment_svc.post(comment=comment, instance_id=instance_id, **fp_ids)
