"""
A script to create or update a form, optionally with attachments.

Either use as a CLI script, or import create_or_update into another module.

If provided, all files in the [attachments_dir] path will be uploaded with the form.
"""

import sys
from os import PathLike
from pathlib import Path

from pyodk.client import Client
from pyodk.errors import PyODKError


def create_ignore_duplicate_error(client: Client, definition: PathLike | str | bytes):
    """Create the form; ignore the error raised if it exists (409.3)."""
    try:
        client.forms.create(definition=definition)
    except PyODKError as err:
        if not err.is_central_error(code=409.3):
            raise


def create_or_update(form_id: str, definition: str, attachments: str | None):
    """Create (and publish) the form, optionally with attachments."""
    with Client() as client:
        create_ignore_duplicate_error(client=client, definition=definition)
        attach = None
        if attachments is not None:
            attach = Path(attachments).iterdir()
        client.forms.update(
            definition=definition,
            form_id=form_id,
            attachments=attach,
        )


if __name__ == "__main__":
    usage = """
Usage:

python create_or_update_form.py form_id definition.xlsx
python create_or_update_form.py form_id definition.xlsx attachments_dir
    """
    if len(sys.argv) < 3:
        print(usage)
        sys.exit(1)
    fid = sys.argv[1]
    def_path = sys.argv[2]
    attach_path = None
    if len(sys.argv) == 4:
        attach_path = sys.argv[3]
    create_or_update(form_id=fid, definition=def_path, attachments=attach_path)
