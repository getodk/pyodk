from pyodk._endpoints.entity_lists import EntityList, log
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
        entity_list = client.session.response_or_error(
            method="POST",
            url=client.session.urlformat(
                "projects/{pid}/datasets",
                pid=client.project_id,
            ),
            logger=log,
            json={"name": entity_list_name},
        )
    except PyODKError:
        entity_list = client.session.get(
            url=client.session.urlformat(
                "projects/{pid}/datasets/{eln}",
                pid=client.project_id,
                eln=entity_list_name,
            ),
        )
    try:
        for prop in entity_props:
            client.session.response_or_error(
                method="GET",
                url=client.session.urlformat(
                    "projects/{pid}/datasets/{eln}/properties",
                    pid=client.project_id,
                    eln=entity_list_name,
                ),
                logger=log,
                json={"name": prop},
            )
    except PyODKError:
        pass
    return EntityList(**entity_list.json())
