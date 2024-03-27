from pydantic import BaseModel

from pyodk._utils.session import Session


class Model(BaseModel):
    """Base configuration for data model classes."""

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True


class Manager:
    """Base for managers of data model classes."""

    __slots__ = ("__weakref__",)

    @classmethod
    def from_dict(cls, session: Session, project_id: int, data: dict) -> Model:
        raise NotImplementedError()


class Service:
    """Base for services interacting with the ODK Central API over HTTP."""

    __slots__ = ("__weakref__",)
