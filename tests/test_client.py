from unittest import TestCase, skip

from pyodk.client import Client


@skip
class TestUsage(TestCase):
    """Tests for experimenting with usage scenarios / general debugging."""

    def test_direct(self):
        with Client() as client:
            projects = client.projects.list()
            forms = client.forms.list()
            submissions = client.submissions.list(form_id=forms[3].xmlFormId)
            form_data = client.submissions.get_table(form_id=forms[3].xmlFormId)
            form_data_params = client.submissions.get_table(
                form_id="range",
                table_name="Submissions",
                count=True,
            )
            comments = client.comments.list(
                project_id=51,
                form_id="range",
                instance_id="uuid:85cb9aff-005e-4edd-9739-dc9c1a829c47",
            )
            print([projects, forms, submissions, form_data, form_data_params, comments])
