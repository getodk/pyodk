import logging
from datetime import datetime

from pyodk._endpoints import bases
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class CurrentVersion(bases.Model):
    label: str
    current: bool
    creatorId: int
    userAgent: str
    version: int
    baseVersion: int | None = None
    conflictingProperties: list[str] | None = None


class Entity(bases.Model):
    uuid: str
    creatorId: int
    createdAt: datetime
    currentVersion: CurrentVersion
    updatedAt: datetime | None = None
    deletedAt: datetime | None = None


class URLs(bases.Model):
    class Config:
        frozen = True

    _entity_name: str = "projects/{project_id}/datasets/{el_name}"
    list: str = f"{_entity_name}/entities"
    post: str = f"{_entity_name}/entities"
    get_table: str = f"{_entity_name}.svc/Entities"


class EntityService(bases.Service):
    """
    Entity-related functionality is accessed through `client.entities`. For example:

    ```python
    from pyodk.client import Client

    client = Client()
    data = client.entities.list()
    ```

    Conceptually, an Entity's parent object is an EntityList. Each EntityList may
    have multiple Entities. In Python parlance, EntityLists are like classes, while
    Entities are like instances.
    """

    __slots__ = ("urls", "session", "default_project_id", "default_entity_list_name")

    def __init__(
        self,
        session: Session,
        default_project_id: int | None = None,
        default_entity_list_name: str | None = None,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session
        self.default_project_id: int | None = default_project_id
        self.default_entity_list_name: str | None = default_entity_list_name

    def list(
        self, entity_list_name: str | None = None, project_id: int | None = None
    ) -> list[Entity]:
        """
        Read all Entity metadata.

        :param entity_list_name: The name of the Entity List (Dataset) being referenced.
        :param project_id: The id of the project the Entity belongs to.

        :return: A list of the object representation of all Entity metadata.
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
            url=self.session.urlformat(self.urls.list, project_id=pid, el_name=eln),
            logger=log,
        )
        data = response.json()
        return [Entity(**r) for r in data]

    def create(
        self,
        label: str,
        data: dict,
        entity_list_name: str | None = None,
        project_id: int | None = None,
        uuid: str | None = None,
    ) -> Entity:
        """
        Create an Entity.

        :param label: Label of the Entity.
        :param data: Data to store for the Entity.
        :param entity_list_name: The name of the Entity List (Dataset) being referenced.
        :param project_id: The id of the project this form belongs to.
        :param uuid: An optional unique identifier for the Entity. If not provided then
          a uuid will be generated and sent by the client.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            eln = pv.validate_entity_list_name(
                entity_list_name, self.default_entity_list_name
            )
            req_data = {
                "uuid": pv.validate_str(uuid, self.session.get_xform_uuid(), key="uuid"),
                "label": pv.validate_str(label, key="label"),
                "data": pv.validate_dict(data, key="data"),
            }
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="POST",
            url=self.session.urlformat(self.urls.post, project_id=pid, el_name=eln),
            logger=log,
            json=req_data,
        )
        data = response.json()
        return Entity(**data)

    def get_table(
        self,
        entity_list_name: str | None = None,
        project_id: int | None = None,
        skip: int | None = None,
        top: int | None = None,
        count: bool | None = None,
        filter: str | None = None,
        select: str | None = None,
    ) -> dict:
        """
        Read Entity List data.

        :param entity_list_name: The name of the Entity List (Dataset) being referenced.
        :param project_id: The id of the project this form belongs to.
        :param skip: The first n rows will be omitted from the results.
        :param top: Only up to n rows will be returned in the results.
        :param count: If True, an @odata.count property will be added to the result to
          indicate the total number of rows, ignoring the above paging parameters.
        :param filter: Filter responses to those matching the query. Only certain fields
          are available to reference. The operators lt, le, eq, neq, ge, gt, not, and,
          and or are supported, and the built-in functions now, year, month, day, hour,
          minute, second.
        :param select: If provided, will return only the selected fields.

        :return: A dictionary representation of the OData JSON document.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            eln = pv.validate_entity_list_name(
                entity_list_name, self.default_entity_list_name
            )
            params = {
                k: v
                for k, v in {
                    "$skip": skip,
                    "$top": top,
                    "$count": count,
                    "$filter": filter,
                    "$select": select,
                }.items()
                if v is not None
            }
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="GET",
            url=self.session.urlformat(
                self.urls.get_table, project_id=pid, el_name=eln, table_name="Entities"
            ),
            logger=log,
            params=params,
        )
        return response.json()
