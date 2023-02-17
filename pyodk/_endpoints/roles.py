import logging
from datetime import datetime
from typing import List, Optional

from pyodk._endpoints import bases
from pyodk._utils.session import Session

log = logging.getLogger(__name__)


class Role(bases.Model):
    id: int
    name: str
    system: str
    verbs: Optional[List[str]]
    createdAt: Optional[datetime]
    updatedAt: Optional[datetime]


class URLs(bases.Model):
    class Config:
        frozen = True

    list: str = "roles"


class RoleService(bases.Service):
    __slots__ = (
        "urls",
        "session",
    )

    def __init__(
        self,
        session: Session,
        urls: URLs = None,
    ):
        self.urls: URLs = urls if urls is not None else URLs()
        self.session: Session = session

    def list(
        self,
    ) -> List[Role]:
        """
        Read all Role details.
        """
        response = self.session.response_or_error(
            method="GET",
            url=self.urls.list,
            logger=log,
        )
        data = response.json()
        return [Role(**r) for r in data]

    def get_role_by_name(self, name: str) -> Optional[Role]:
        """
        Look up the given name and return corresponding Role info, if any.

        :param name: The role name to look up.
        :return: The Role, or raise an error if not found.
        """
        role_matches = [r for r in self.list() if r.name == name]
        if 1 == len(role_matches):
            return role_matches[0]
