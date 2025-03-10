from pyodk._endpoints.entity_lists import EntityList
from pyodk.client import Client
from pyodk.errors import PyODKError


def create_new_or_get_entity_list(
    client: Client, entity_list_name: str, entity_props: list[str]
) -> EntityList:
    """
    Create a new entity list, or get the entity list metadata.

    :param client: Client instance to use for API calls.
    :param entity_list_name: Name of the entity list.
    :param entity_props: Properties to add to the entity list.
    """
    try:
        entity_list = client.entity_lists.create(entity_list_name=entity_list_name)
    except PyODKError as err:
        if not err.is_central_error(code=409.3):
            raise
        entity_list = EntityList(
            **client.session.get(
                url=client.session.urlformat(
                    "projects/{pid}/datasets/{eln}",
                    pid=client.project_id,
                    eln=entity_list_name,
                ),
            ).json()
        )
    try:
        for prop in entity_props:
            client.entity_lists.add_property(name=prop, entity_list_name=entity_list_name)
    except PyODKError as err:
        if not err.is_central_error(code=409.3):
            raise
    return entity_list
