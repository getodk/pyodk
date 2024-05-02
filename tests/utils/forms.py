from pyodk.client import Client
from pyodk.errors import PyODKError

from tests.utils import utils
from tests.utils.md_table import md_table_to_temp_dir


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
        try:
            client.forms.create(definition=fp, form_id=form_id)
        except PyODKError:
            pass


def create_new_form__xml(client: Client, form_id: str, form_def: str):
    """
    Create a new form from a XML string.

    :param client: Client instance to use for API calls.
    :param form_id: The xmlFormId of the Form being referenced.
    :param form_def: The form definition XML.
    """
    with utils.get_temp_file(suffix=".xml") as fp:
        fp.write_text(form_def)
        try:
            client.forms.create(definition=fp, form_id=form_id)
        except PyODKError:
            pass


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
