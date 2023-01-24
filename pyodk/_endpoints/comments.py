import logging
from datetime import datetime
from typing import List, Optional

from pyodk._endpoints import bases
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class Comment(bases.Model):
    body: str
    actorId: int
    createdAt: datetime


class URLs(bases.Model):
    class Config:
        frozen = True

    list: str = "projects/{project_id}/forms/{form_id}/submissions/{instance_id}/comments"
    post: str = "projects/{project_id}/forms/{form_id}/submissions/{instance_id}/comments"


class CommentService(bases.Service):
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
        default_project_id: Optional[int] = None,
        default_form_id: Optional[str] = None,
        default_instance_id: Optional[str] = None,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session
        self.default_project_id: Optional[int] = default_project_id
        self.default_form_id: Optional[str] = default_form_id
        self.default_instance_id: Optional[str] = default_instance_id

    def list(
        self,
        form_id: Optional[str] = None,
        project_id: Optional[int] = None,
        instance_id: Optional[str] = None,
    ) -> List[Comment]:
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
            raise err

        response = self.session.response_or_error(
            method="GET",
            url=self.urls.list.format(project_id=pid, form_id=fid, instance_id=iid),
            logger=log,
        )
        data = response.json()
        return [Comment(**r) for r in data]

    def post(
        self,
        comment: str,
        project_id: Optional[int] = None,
        form_id: Optional[str] = None,
        instance_id: Optional[str] = None,
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
            comment = pv.wrap_error(
                validator=pv.v.str_validator, key="comment", value=comment
            )
            json = {"body": comment}
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise err

        response = self.session.response_or_error(
            method="POST",
            url=self.urls.post.format(project_id=pid, form_id=fid, instance_id=iid),
            logger=log,
            json=json,
        )
        data = response.json()
        return Comment(**data)
