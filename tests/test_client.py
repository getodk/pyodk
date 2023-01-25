from unittest import TestCase, skip

from pyodk.client import Client


@skip
class TestUsage(TestCase):
    """Tests for experimenting with usage scenarios / general debugging."""

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
