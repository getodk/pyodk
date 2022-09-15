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
            form_data = client.submissions.get_data(form_id=forms[3].xmlFormId)
            form_data_params = client.submissions.get_data(
                form_id="range",
                table_name="Submissions",
                count=True,
            )
            form_odata_metadata = client.forms.get_metadata(form_id="range")
            print(
                [
                    projects,
                    forms,
                    submissions,
                    form_data,
                    form_data_params,
                    form_odata_metadata,
                ]
            )

    def test_fluent(self):
        with Client() as client:
            project = client.projects.get(8)
            form = client.projects.get(8).m.forms.get("range")
            submission = (
                client.projects.get(8).m.forms.get("range").m.submissions.list()[0]
            )
            print(project.dict(), form.dict(), submission.dict())
