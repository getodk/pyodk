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
                form_id="range", table_name="Submissions", params={"$top": 2}
            )
            print([projects, forms, submissions, odata, odata_filter])
