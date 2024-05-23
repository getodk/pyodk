from uuid import uuid4

from pyodk.client import Client
from pyodk.errors import PyODKError

from tests.resources import submissions_data
from tests.utils.forms import get_latest_form_version


def create_new_or_get_last_submission(
    client: Client, form_id: str, instance_id: str
) -> str:
    """
    Create a new submission, or get the most recent version, and return it's instance_id.

    :param client: Client instance to use for API calls.
    :param form_id: The xmlFormId of the Form being referenced.
    :param instance_id: The instanceId of the Submission being referenced.
    :return: The created instance_id or the instance_id of the most recent version.
    """
    try:
        old_iid = client.submissions.create(
            xml=submissions_data.get_xml__fruits(
                form_id=form_id,
                version=get_latest_form_version(client=client, form_id=form_id),
                instance_id=instance_id,
            ),
            form_id=form_id,
        ).instanceId
    except PyODKError as err:
        if not err.is_central_error(code=409.3):
            raise
        subvs = client.session.get(
            client.session.urlformat(
                "projects/{pid}/forms/{fid}/submissions/{iid}/versions",
                pid=client.project_id,
                fid=form_id,
                iid=instance_id,
            ),
        )
        old_iid = sorted(
            (s for s in subvs.json()), key=lambda s: s["createdAt"], reverse=True
        )[0]["instanceId"]
    return old_iid


def create_or_update_submission_with_comment(
    client: Client, form_id: str, instance_id: str
):
    """
    Create and/or update a submission, adding a comment with the edit.

    :param client: Client instance to use for API calls.
    :param form_id: The xmlFormId of the Form being referenced.
    :param instance_id: The instanceId of the Submission being referenced.
    """
    pd_iid = create_new_or_get_last_submission(
        client=client,
        form_id=form_id,
        instance_id=instance_id,
    )
    client.submissions.edit(
        xml=submissions_data.get_xml__fruits(
            form_id=form_id,
            version=get_latest_form_version(client=client, form_id=form_id),
            instance_id=uuid4().hex,
            deprecated_instance_id=pd_iid,
        ),
        form_id=form_id,
        instance_id=instance_id,
        comment="pyODK edit",
    )
