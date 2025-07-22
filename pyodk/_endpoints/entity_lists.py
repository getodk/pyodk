import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pyodk._endpoints.bases import Model, Service
from pyodk._endpoints.entity_list_properties import (
    EntityListProperty,
    EntityListPropertyService,
)
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class EntityList(Model):
    name: str
    projectId: int
    createdAt: datetime
    approvalRequired: bool
    properties: list[EntityListProperty] | None = None


@dataclass(frozen=True, slots=True)
class URLs:
    _entity_list = "projects/{project_id}/datasets"
    list: str = _entity_list
    post: str = _entity_list
    get: str = f"{_entity_list}/{{entity_list_name}}"


class EntityListService(Service):
    """
    Entity List-related functionality is accessed through `client.entity_lists`.

    For example:

    ```python
    from pyodk.client import Client

    client = Client()
    data = client.entity_lists.list()
    ```

    Conceptually, an EntityList's parent object is a Project. Each Project may have
    multiple EntityLists.
    """

    __slots__ = (
        "_default_entity_list_name",
        "_default_project_id",
        "_property_service",
        "add_property",
        "session",
        "urls",
    )

    def __init__(
        self,
        session: Session,
        default_project_id: int | None = None,
        default_entity_list_name: str | None = None,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session
        self._property_service = EntityListPropertyService(
            session=self.session,
            default_project_id=default_project_id,
            default_entity_list_name=default_entity_list_name,
        )
        self.add_property = self._property_service.create

        self._default_project_id: int | None = None
        self.default_project_id = default_project_id
        self._default_entity_list_name: str | None = None
        self.default_entity_list_name = default_entity_list_name

    def _default_kw(self) -> dict[str, Any]:
        return {
            "default_project_id": self.default_project_id,
            "default_entity_list_name": self.default_entity_list_name,
        }

    @property
    def default_project_id(self) -> int | None:
        return self._default_project_id

    @default_project_id.setter
    def default_project_id(self, v) -> None:
        self._default_project_id = v
        self._property_service.default_project_id = v

    @property
    def default_entity_list_name(self) -> str | None:
        return self._default_entity_list_name

    @default_entity_list_name.setter
    def default_entity_list_name(self, v) -> None:
        self._default_entity_list_name = v
        self._property_service.default_entity_list_name = v

    def list(self, project_id: int | None = None) -> list[EntityList]:
        """
        Read all Entity List details.

        :param project_id: The id of the project the Entity List belongs to.

        :return: A list of the object representation of all Entity Lists' details.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="GET",
            url=self.session.urlformat(self.urls.list, project_id=pid),
            logger=log,
        )
        data = response.json()
        return [EntityList(**r) for r in data]

    def get(
        self,
        entity_list_name: str | None = None,
        project_id: int | None = None,
    ) -> EntityList:
        """
        Read Entity List details.

        :param project_id: The id of the project the Entity List belongs to.
        :param entity_list_name: The name of the Entity List (Dataset) being referenced.

        :return: An object representation of all Entity Lists' details.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            eln = pv.validate_entity_list_name(
                entity_list_name, self.default_entity_list_name
            )
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="GET",
            url=self.session.urlformat(
                self.urls.get, project_id=pid, entity_list_name=eln
            ),
            logger=log,
        )
        data = response.json()
        return EntityList(**data)

    def create(
        self,
        approval_required: bool | None = False,
        entity_list_name: str | None = None,
        project_id: int | None = None,
    ) -> EntityList:
        """
        Create an Entity List.

        :param approval_required: If False, create Entities as soon as Submissions are
          received by Central. If True, create Entities when Submissions are marked as
          Approved in Central.
        :param entity_list_name: The name of the Entity List (Dataset) being referenced.
        :param project_id: The id of the project this Entity List belongs to.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            req_data = {
                "name": pv.validate_entity_list_name(
                    entity_list_name, self.default_entity_list_name
                ),
                "approvalRequired": pv.validate_bool(
                    approval_required, key="approval_required"
                ),
            }
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="POST",
            url=self.session.urlformat(self.urls.post, project_id=pid),
            logger=log,
            json=req_data,
        )
        data = response.json()
        return EntityList(**data)
