import logging
from dataclasses import dataclass
from datetime import datetime

from pyodk._endpoints.bases import Model, Service
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class Comment(Model):
    body: str
    actorId: int
    createdAt: datetime


@dataclass(frozen=True, slots=True)
class URLs:
    list: str = "projects/{project_id}/forms/{form_id}/submissions/{instance_id}/comments"
    post: str = "projects/{project_id}/forms/{form_id}/submissions/{instance_id}/comments"


class CommentService(Service):
    __slots__ = (
        "urls",
        "session",
        "default_project_id",
        "default_form_id",
        "default_instance_id",
    )

    def __init__(
        self,
        session: Session,
        default_project_id: int | None = None,
        default_form_id: str | None = None,
        default_instance_id: str | None = None,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session
        self.default_project_id: int | None = default_project_id
        self.default_form_id: str | None = default_form_id
        self.default_instance_id: str | None = default_instance_id

    def list(
        self,
        form_id: str | None = None,
        project_id: int | None = None,
        instance_id: str | None = None,
    ) -> list[Comment]:
        """
        Read all Comment details.

        :param form_id: The xmlFormId of the Form being referenced.
        :param project_id: The id of the project the Submissions belong to.
        :param instance_id: The instanceId of the Submission being referenced.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            iid = pv.validate_instance_id(instance_id, self.default_instance_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="GET",
            url=self.session.urlformat(
                self.urls.list, project_id=pid, form_id=fid, instance_id=iid
            ),
            logger=log,
        )
        data = response.json()
        return [Comment(**r) for r in data]

    def post(
        self,
        comment: str,
        project_id: int | None = None,
        form_id: str | None = None,
        instance_id: str | None = None,
    ) -> Comment:
        """
        Create a Comment.

        :param comment: The text of the comment.
        :param project_id: The id of the project this form belongs to.
        :param form_id: The xmlFormId of the Form being referenced.
        :param instance_id: The instanceId of the Submission being referenced.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            fid = pv.validate_form_id(form_id, self.default_form_id)
            iid = pv.validate_instance_id(instance_id, self.default_instance_id)
            comment = pv.validate_str(comment, key="comment")
            json = {"body": comment}
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="POST",
            url=self.session.urlformat(
                self.urls.post, project_id=pid, form_id=fid, instance_id=iid
            ),
            logger=log,
            json=json,
        )
        data = response.json()
        return Comment(**data)
