from unittest import TestCase, skip

from pyodk.client import Client


@skip
class TestUsage(TestCase):
    def test_usage(self):
        with Client() as client:
            projects = client.projects.read_all()
            forms = client.forms.read_all()
            submissions = client.submissions.read_all(form_id=forms[3].xmlFormId)
            odata = client.odata.read_table(form_id=forms[3].xmlFormId)
            odata_filter = client.odata.read_table(
                form_id="range",
                table_name="Submissions",
                count=True,
            )
            odata_metadata = client.odata.read_metadata(form_id="range")
            print([projects, forms, submissions, odata, odata_filter, odata_metadata])
