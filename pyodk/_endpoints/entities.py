import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from pyodk.__version__ import __version__
from pyodk._endpoints.bases import Model, Service
from pyodk._endpoints.entity_list_properties import EntityListPropertyService
from pyodk._utils import validators as pv
from pyodk._utils.session import Session
from pyodk.errors import PyODKError

log = logging.getLogger(__name__)
SENTINEL = object()


@dataclass
class MergeActions:
    """Return type for EntityService._prep_data_for_merge / merge"""

    match_keys: list
    to_insert: dict = field(default_factory=dict)
    to_update: dict = field(default_factory=dict)
    to_delete: dict = field(default_factory=dict)
    source_keys: set = field(default_factory=set)
    target_keys: set = field(default_factory=set)
    reserved_keys: frozenset = frozenset({"__id", "__system", "label"})
    # Set by "merge" function according to the "add_new_properties" parameter.
    final_keys: set = field(default_factory=set)

    @property
    def keys_difference(self) -> set:
        return (self.source_keys - self.target_keys) - self.reserved_keys

    @property
    def keys_intersect(self) -> set:
        return (self.source_keys & self.target_keys) - self.reserved_keys

    @property
    def keys_union(self) -> set:
        return (self.source_keys | self.target_keys) - self.reserved_keys


class CurrentVersion(Model):
    label: str
    current: bool
    createdAt: datetime
    creatorId: int
    userAgent: str
    version: int
    data: dict | None = None
    baseVersion: int | None = None
    conflictingProperties: list[str] | None = None


class Entity(Model):
    uuid: str
    creatorId: int
    createdAt: datetime
    currentVersion: CurrentVersion
    conflict: str | None = None  # null, soft, hard
    updatedAt: datetime | None = None
    deletedAt: datetime | None = None


@dataclass(frozen=True, slots=True)
class URLs:
    _entity_name: str = "projects/{project_id}/datasets/{el_name}"
    _entities: str = f"{_entity_name}/entities"
    list: str = _entities
    post: str = _entities
    patch: str = f"{_entities}/{{entity_id}}"
    delete: str = patch
    get_table: str = f"{_entity_name}.svc/Entities"


class EntityService(Service):
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

    __slots__ = ("default_entity_list_name", "default_project_id", "session", "urls")

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
        :param project_id: The id of the project this Entity belongs to.
        :param uuid: An optional unique identifier for the Entity. If not provided then
          a uuid will be generated and sent by the client.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            eln = pv.validate_entity_list_name(
                entity_list_name, self.default_entity_list_name
            )
            req_data = {
                # For entities, Central creates a literal uuid, not an XForm uuid:uuid4()
                "uuid": pv.validate_str(uuid, str(uuid4()), key="uuid"),
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

    def create_many(
        self,
        data: Iterable[Mapping[str, Any]],
        entity_list_name: str | None = None,
        project_id: int | None = None,
        create_source: str | None = None,
        source_size: str | None = None,
    ) -> bool:
        """
        Create one or more Entities in a single request.

        Example input for `data` would be a list of dictionaries from a CSV file:

        data = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
            {"label": "Melbourne", "state": "VIC", "postcode": "3000"},
        ]

        Each Entity in `data` must include a "label" key. An Entity List property must be
        created in advance for each key in `data` that is not "label". The `merge` method
        can be used to automatically add properties (or a subset) and create Entities.

        :param data: Data to store for the Entities.
        :param entity_list_name: The name of the Entity List (Dataset) being referenced.
        :param project_id: The id of the project this Entity belongs to.
        :param create_source: Used to capture the source of the change in Central, for
          example a file name. Defaults to the PyODK version.
        :param source_size: Used to capture the size of the source data in Central, for
          example a file size or row count. Excluded if None.
        """
        if create_source is None:
            create_source = f"pyodk v{__version__}"
        if source_size is None:
            size = {}
        else:
            size = {"size": source_size}

        def reshape(d):
            try:
                new = [
                    {
                        "label": i["label"],
                        "data": {k: i.get(k) for k in i if k != "label"},
                    }
                    for i in d
                ]
            except KeyError as kerr:
                raise PyODKError("All data must include a 'label' key.") from kerr
            else:
                return new

        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            eln = pv.validate_entity_list_name(
                entity_list_name, self.default_entity_list_name
            )
            data = pv.validate_is_instance(data, typ=Iterable, key="data")
            final_data = {
                "entities": reshape(data),
                "source": {"name": create_source, **size},
            }
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="POST",
            url=self.session.urlformat(self.urls.post, project_id=pid, el_name=eln),
            logger=log,
            json=final_data,
        )
        data = response.json()
        return data["success"]

    def update(
        self,
        uuid: str,
        entity_list_name: str | None = None,
        project_id: int | None = None,
        label: str | None = None,
        data: dict | None = None,
        force: bool | None = None,
        base_version: int | None = None,
    ) -> Entity:
        """
        Update an Entity.

        :param uuid: The unique identifier for the Entity.
        :param label: Label of the Entity.
        :param data: Data to store for the Entity.
        :param force: If True, update an Entity regardless of its current state. If
          `base_version` is not specified, then `force` must be True.
        :param base_version: The expected current version of the Entity on the server. If
          `force` is not True, then `base_version` must be specified.
        :param entity_list_name: The name of the Entity List (Dataset) being referenced.
        :param project_id: The id of the project this Entity belongs to.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            eln = pv.validate_entity_list_name(
                entity_list_name, self.default_entity_list_name
            )
            eid = pv.validate_str(uuid, key="uuid")
            params = {}
            if force is not None:
                params["force"] = pv.validate_bool(force, key="force")
            if base_version is not None:
                params["baseVersion"] = pv.validate_int(base_version, key="base_version")
            if len([i for i in (force, base_version) if i is not None]) != 1:
                raise PyODKError("Must specify one of 'force' or 'base_version'.")  # noqa: TRY301
            req_data = {}
            if label is not None:
                req_data["label"] = pv.validate_str(label, key="label")
            if data is not None:
                req_data["data"] = pv.validate_dict(data, key="data")
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="PATCH",
            url=self.session.urlformat(
                self.urls.patch, project_id=pid, el_name=eln, entity_id=eid
            ),
            logger=log,
            params=params,
            json=req_data,
        )
        data = response.json()
        return Entity(**data)

    def delete(
        self,
        uuid: str,
        entity_list_name: str | None = None,
        project_id: int | None = None,
    ) -> bool:
        """
        Delete an Entity.

        :param uuid: The unique identifier for the Entity.
        :param entity_list_name: The name of the Entity List (Dataset) being referenced.
        :param project_id: The id of the project this Entity belongs to.
        """
        try:
            pid = pv.validate_project_id(project_id, self.default_project_id)
            eln = pv.validate_entity_list_name(
                entity_list_name, self.default_entity_list_name
            )
            eid = pv.validate_str(uuid, key="uuid")
        except PyODKError as err:
            log.error(err, exc_info=True)
            raise

        response = self.session.response_or_error(
            method="DELETE",
            url=self.session.urlformat(
                self.urls.delete, project_id=pid, el_name=eln, entity_id=eid
            ),
            logger=log,
        )
        data = response.json()
        return data["success"]

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
        :param project_id: The id of the project this Entity belongs to.
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

    @staticmethod
    def _prep_data_for_merge(
        source_data: Iterable[Mapping[str, Any]],
        target_data: Iterable[Mapping[str, Any]],
        match_keys: Iterable[str] | None = None,
        source_label_key: str = "label",
        source_keys: Iterable[str] | None = None,
    ) -> MergeActions:
        """
        Compare source and target data to identify rows to insert, update, or delete.

        :param source_data: Incoming data to be sent to the target database.
        :param target_data: Existing data from the target database.
        :param match_keys: Dictionary keys common to source and target used to match rows.
        :param source_label_key: The key in the source data to use as the label.
        :param source_keys: If provided, process only these keys in the source data.
        """
        default_key = "label"
        if source_label_key is None:
            source_label_key = default_key
        if match_keys is None:
            match_keys = (default_key,)
        match_keys_sorted = sorted(match_keys)

        if source_keys is not None and source_label_key not in source_keys:
            raise PyODKError(
                "Parameter 'source_keys' must include \"label\" or the "
                "'source_label_key' parameter value"
            )

        def get_key(entity: Mapping[str, Any], keys: list) -> tuple:
            try:
                return tuple(entity[i] for i in keys)
            except KeyError as e:
                raise PyODKError(
                    f"Found Entity that did not have all expected match_keys: {e}"
                ) from e

        result = MergeActions(match_keys=match_keys_sorted)
        # Dict conversion uses memory, but original list of dict has worst case O(n*m).
        src = {}
        source_data_len = 0  # Not using len() since it might not be a collection.
        for s in source_data:
            row = {default_key: s[source_label_key]}
            if source_keys is None:
                row.update({k: s[k] for k in s if k != source_label_key})
            else:
                row.update(
                    {k: s[k] for k in s if k != source_label_key and k in source_keys}
                )
            src[get_key(row, match_keys_sorted)] = row
            result.source_keys.update(row.keys())
            source_data_len += 1

        if len(src) != source_data_len:
            raise PyODKError(
                "Parameter 'match_keys' not unique across all 'source_data'."
            )

        for t in target_data:
            key = get_key(t, match_keys_sorted)
            result.target_keys.update(t.keys())
            match = src.pop(key, None)
            if match is None:
                result.to_delete[key] = t
            else:
                for_update = False
                new_data = {}
                for k, v in t.items():
                    # Add all the ID fields from the target data.
                    if k in result.reserved_keys:
                        new_data[k] = v
                        continue
                    # Ignore values where source has no key (nothing to update).
                    # Uses sentinel differentiate None as a value, without a keys check.
                    new_value = match.get(k, SENTINEL)
                    if new_value is SENTINEL:
                        continue
                    # Add the source value if it is different.
                    # Entity values are stored in Central as strings.
                    if str(new_value) != v:
                        new_data[k] = new_value
                        for_update = True
                for k, v in match.items():
                    # Add values for any new keys not in the target.
                    if k not in t:
                        new_data[k] = v
                        for_update = True
                if for_update:
                    result.to_update[key] = new_data

        result.to_insert = src
        return result

    def merge(
        self,
        data: Iterable[Mapping[str, Any]],
        entity_list_name: str | None = None,
        project_id: int | None = None,
        match_keys: Iterable[str] | None = None,
        add_new_properties: bool = True,
        update_matched: bool = True,
        delete_not_matched: bool = False,
        source_label_key: str = "label",
        source_keys: Iterable[str] | None = None,
        create_source: str | None = None,
        source_size: str | None = None,
    ) -> MergeActions:
        """
        Update Entities in Central based on the provided data:

        1. Create Entities from `data` that don't exist in Central.
        2. Update Entities from `data` that exist in Central.
        3. Optionally, delete any Entities in Central that don't exist in `data`.

        Example input for `source_data` would be a list of dictionaries from a CSV file:

        data = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
            {"label": "Melbourne", "state": "VIC", "postcode": "3000"},
        ]

        Entity creation is performed in one request using `create_many`. The merge
        operation may be slow if large quantities of updates or deletes are required,
        since for these operations each change is a request in a loop. If this is a
        concern, set the parameters `update_matched` and `delete_not_matched` to False and
        use the return value to perform threaded or async requests for these data.

        :param data: Data to use for updating Entities in Central.
        :param entity_list_name: The name of the Entity List (Dataset) being referenced.
        :param project_id: The id of the project this Entity belongs to.
        :param match_keys: Dictionary keys common to source and target used to match rows.
          Defaults to ("label",). If a custom source_label_key is provided, specify that
          key as "label", because it is translated to "label" for matching.
        :param add_new_properties: If True, add any Entity List properties from `data`
          that aren't in Central.
        :param update_matched: If True, update any Entities in Central that match `data`
          but have different properties.
        :param delete_not_matched: If True, delete any Entities in Central that aren't
          in `data`.
        :param source_label_key: The key in `data` to use as the label. The target label
          key is always "label" because this key is required by Central.
        :param source_keys: If provided, process only these keys in `data`.
        :param create_source: If Entities are created, this is used to capture the source
          of the change in Central, for example a file name. Defaults to the PyODK version.
        :param source_size: If Entities are created, this is used to capture the size of
          `data` in Central, for example a file size. Excluded if None.
        """
        pid = pv.validate_project_id(project_id, self.default_project_id)
        eln = pv.validate_entity_list_name(
            entity_list_name, self.default_entity_list_name
        )
        target_data = self.get_table(entity_list_name=entity_list_name)["value"]
        merge_actions = self._prep_data_for_merge(
            source_data=data,
            target_data=target_data,
            match_keys=match_keys,
            source_label_key=source_label_key,
            source_keys=source_keys,
        )
        if add_new_properties:
            elps = EntityListPropertyService(
                session=self.session,
                default_project_id=pid,
                default_entity_list_name=eln,
            )
            for k in merge_actions.keys_difference:
                elps.create(name=k)
            merge_actions.final_keys = merge_actions.keys_union
        else:
            merge_actions.final_keys = merge_actions.keys_intersect
        if len(merge_actions.to_insert) > 0:
            relevant_keys = {"label", *merge_actions.final_keys}
            insert_filter = [
                {k: i.get(k) for k in i if k in relevant_keys}
                for i in merge_actions.to_insert.values()
            ]
            self.create_many(
                data=insert_filter,
                entity_list_name=eln,
                create_source=create_source,
                source_size=source_size,
            )
        if update_matched:
            for u in merge_actions.to_update.values():
                self.update(
                    uuid=u["__id"],
                    entity_list_name=eln,
                    label=u["label"],
                    data={k: u.get(k) for k in u if k in merge_actions.final_keys},
                    base_version=u["__system"]["version"],
                )
        if delete_not_matched:
            for d in merge_actions.to_delete.values():
                self.delete(uuid=d["__id"], entity_list_name=eln)
        return merge_actions
