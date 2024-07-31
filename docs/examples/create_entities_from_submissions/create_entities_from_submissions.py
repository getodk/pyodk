"""
A script that uses CSV data to create an entity list and populate it with entities.
"""

from csv import DictReader
from pathlib import Path
from uuid import uuid4

from pyodk import Client

project_id = 1
entity_list_name = f"previous_survey_{uuid4()}"
entity_label_field = "first_name"
entity_properties = ("age", "location")
csv_path = Path("./imported_answers.csv")


def create_one_at_a_time():
    with Client(project_id=project_id) as client, open(csv_path) as csv_file:
        # Create the entity list.
        client.entity_lists.create(entity_list_name=entity_list_name)
        for prop in entity_properties:
            client.entity_lists.add_property(name=prop, entity_list_name=entity_list_name)

        # Create the entities from the CSV data.
        for row in DictReader(csv_file):
            client.entities.create(
                label=row[entity_label_field],
                data={k: str(v) for k, v in row.items() if k in entity_properties},
                entity_list_name=entity_list_name,
            )


def create_with_merge():
    with Client(project_id=project_id) as client, open(csv_path) as csv_file:
        client.entity_lists.default_entity_list_name = client.session.get_xform_uuid()
        entity_list = client.entity_lists.create()
        client.entities.merge(
            source_data=list(DictReader(csv_file)),
            entity_list_name=entity_list.name,
            source_label_key=entity_label_field,
            source_keys=entity_properties,
        )


if __name__ == "__main__":
    # create_one_at_a_time()
    create_with_merge()
