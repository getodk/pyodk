from pathlib import Path
from typing import IO

from pyodk._endpoints.form_drafts import FormDraftService
from pyodk.client import Client
from pyodk.errors import PyODKError

from tests.utils import utils
from tests.utils.md_table import md_table_to_temp_dir


def create_new_form(client: Client, file_path: Path | str, form_id: str, form_data: IO):
    """
    Create a new form. Ignores any pyODK errors.

    :param client: Client instance to use for API calls.
    :param file_path: Path of the form definition.
    :param form_id: The xmlFormId of the Form being referenced.
    :param form_data: The form file descriptor which can be read() from.
    :return:
    """
    try:
        fd = FormDraftService(
            session=client.session, default_project_id=client.project_id
        )
        pid, fid, headers, params = fd._prep_form_post(
            file_path=file_path, form_id=form_id
        )
        params["publish"] = True
        client.post(
            url=client.session.urlformat("projects/{pid}/forms", pid=client.project_id),
            headers=headers,
            params=params,
            data=form_data,
        )
    except PyODKError:
        pass


def create_new_form__md(client: Client, form_id: str, form_def: str):
    """
    Create a new form from a MarkDown string.

    :param client: Client instance to use for API calls.
    :param form_id: The xmlFormId of the Form being referenced.
    :param form_def: The form definition MarkDown.
    """
    with (
        md_table_to_temp_dir(form_id=form_id, mdstr=form_def) as fp,
        open(fp, "rb") as form_data,
    ):
        create_new_form(client=client, file_path=fp, form_id=form_id, form_data=form_data)


def create_new_form__xml(client: Client, form_id: str, form_def: str):
    """
    Create a new form from a XML string.

    :param client: Client instance to use for API calls.
    :param form_id: The xmlFormId of the Form being referenced.
    :param form_def: The form definition XML.
    """
    with utils.get_temp_file(suffix=".xml") as fp:
        fp.write_text(form_def)
        with open(fp, "rb") as form_data:
            create_new_form(
                client=client, file_path=fp, form_id=form_id, form_data=form_data
            )


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
