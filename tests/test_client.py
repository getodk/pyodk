from unittest import TestCase, skip

from pyodk.client import Client
from tests.resources import RESOURCES


@skip
class TestUsage(TestCase):
    """Tests for experimenting with usage scenarios / general debugging / integration."""

    def test_direct(self):
        client = Client()
        projects = client.projects.list()
        forms = client.forms.list()
        submissions = client.submissions.list(form_id=forms[3].xmlFormId)
        form_data = client.submissions.get_table(form_id=forms[3].xmlFormId)
        form_data_params = client.submissions.get_table(
            form_id="range",
            table_name="Submissions",
            count=True,
        )
        comments = client.submissions.list_comments(
            form_id="range",
            instance_id="uuid:2c296eae-2708-4a89-bfe7-0f2d440b7fe8",
        )
        print([projects, forms, submissions, form_data, form_data_params, comments])

    def test_direct_context(self):
        with Client() as client:
            projects = client.projects.list()
            forms = client.forms.list()
        print(projects, forms)

    # form_update tests assume project has forms by these names already published.
    def test_form_update__new_definition(self):
        """Should create a new version with the new definition."""
        with Client() as client:
            client.forms.update(
                form_id="range_draft",
                definition=(RESOURCES / "forms" / "range_draft.xml").as_posix(),
            )

    def test_form_update__new_definition_and_attachments(self):
        """Should create a new version with new definition and attachment."""
        with Client() as client:
            client.forms.update(
                form_id="pull_data",
                definition=(RESOURCES / "forms" / "pull_data.xlsx").as_posix(),
                attachments=[(RESOURCES / "forms" / "fruits.csv").as_posix()],
            )

    def test_form_update__attachments(self):
        """Should create a new version with new attachment."""
        with Client() as client:
            client.forms.update(
                form_id="pull_data",
                attachments=[(RESOURCES / "forms" / "fruits.csv").as_posix()],
            )
