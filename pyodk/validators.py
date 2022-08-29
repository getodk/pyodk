from typing import Optional

from pyodk.errors import PyODKError
from pyodk.utils import coalesce


def validate_project_id(
    project_id: Optional[int] = None, default_project_id: Optional[int] = None
) -> int:
    pid = coalesce(project_id, default_project_id)
    if pid is None:
        msg = "No project ID was provided, either directly or via a default setting."
        raise PyODKError(msg)
    return pid


def validate_form_id(form_id: Optional[str] = None) -> str:
    if form_id is None:
        msg = "No form ID was provided."
        raise PyODKError(msg)
    return form_id


def validate_table_name(table_name: Optional[str] = None) -> str:
    if table_name is None:
        msg = "No table name was provided."
        raise PyODKError(msg)
    return table_name


def validate_instance_id(instance_id: Optional[str] = None) -> str:
    if instance_id is None:
        msg = "No instance ID was provided."
        raise PyODKError(msg)
    return instance_id
