from unittest import TestCase, skip

from pyodk.client import Client


@skip
class TestUsage(TestCase):
    """Tests for experimenting with usage scenarios / general debugging."""

    def test_direct(self):
        with Client() as client:
            projects = client.projects.read_all()
            forms = client.forms.read_all()
            submissions = client.submissions.read_all(form_id=forms[3].xmlFormId)
            form_data = client.submissions.read_all_table(form_id=forms[3].xmlFormId)
            form_data_params = client.submissions.read_all_table(
                form_id="range",
                table_name="Submissions",
                count=True,
            )
            form_odata_metadata = client.forms.read_odata_metadata(form_id="range")
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
            project = client.projects.read(8)
            form = client.projects.read(8).m.forms.read("range")
            submission = (
                client.projects.read(8).m.forms.read("range").m.submissions.read_all()[0]
            )
            print(project.dict(), form.dict(), submission.dict())
