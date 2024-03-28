import logging
from datetime import datetime

from pyodk._endpoints import bases
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)


class EntityList(bases.Model):
    name: str
    projectId: int
    createdAt: datetime
    approvalRequired: bool


class URLs(bases.Model):
    class Config:
        frozen = True

    list: str = "projects/{project_id}/datasets"


class EntityListService(bases.Service):
    """
    Entity List-related functionality is accessed through `client.entity_lists`.

    For example:

    ```python
    from pyodk.client import Client

    client = Client()
    data = client.entity_lists.list()
    ```

    The structure this class works with is conceptually a list of lists, e.g.

    ```
    EntityList = list[Entity]
    self.list() = list[EntityList]
    ```
    """

    __slots__ = ("urls", "session", "default_project_id")

    def __init__(
        self,
        session: Session,
        default_project_id: int | None = None,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session
        self.default_project_id: int | None = default_project_id

    def list(self, project_id: int | None = None) -> list[EntityList]:
        """
        Read Entity List details.

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
