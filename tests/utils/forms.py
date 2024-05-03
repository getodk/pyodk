from os import PathLike

from pyodk.client import Client
from pyodk.errors import PyODKError
from requests import Response

from tests.utils import utils
from tests.utils.md_table import md_table_to_temp_dir


def create_ignore_duplicate_error(
    client: Client,
    definition: PathLike | str | bytes,
    form_id: str,
):
    """Create the form; ignore the error raised if it exists (409.3)."""
    try:
        client.forms.create(definition=definition, form_id=form_id)
    except PyODKError as err:
        if len(err.args) >= 2 and isinstance(err.args[1], Response):
            err_detail = err.args[1].json()
            err_code = err_detail.get("code")
            if err_code is not None and str(err_code) == "409.3":
                return
        raise


def create_new_form__md(client: Client, form_id: str, form_def: str):
    """
    Create a new form from a MarkDown string.

    :param client: Client instance to use for API calls.
    :param form_id: The xmlFormId of the Form being referenced.
    :param form_def: The form definition MarkDown.
    """
    with (
        md_table_to_temp_dir(form_id=form_id, mdstr=form_def) as fp,
    ):
        create_ignore_duplicate_error(client=client, definition=fp, form_id=form_id)


def create_new_form__xml(client: Client, form_id: str, form_def: str):
    """
    Create a new form from a XML string.

    :param client: Client instance to use for API calls.
    :param form_id: The xmlFormId of the Form being referenced.
    :param form_def: The form definition XML.
    """
    with utils.get_temp_file(suffix=".xml") as fp:
        fp.write_text(form_def)
        create_ignore_duplicate_error(client=client, definition=fp, form_id=form_id)


def get_latest_form_version(client: Client, form_id: str) -> str:
    """
    Get the version name of the most recently published version of the form.

    :param client: Client instance to use for API calls.
    :param form_id: The xmlFormId of the Form being referenced.
    """
    versions = client.session.get(
        client.session.urlformat(
            "projects/{pid}/forms/{fid}/versions",
            pid=client.project_id,
            fid=form_id,
        )
    )
    return sorted(
        (s for s in versions.json()), key=lambda s: s["publishedAt"], reverse=True
    )[0]["version"]
