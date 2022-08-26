from unittest import TestCase, skip

from pyodk.client import Client


@skip
class TestUsage(TestCase):
    def test_usage(self):
        with Client() as client:
            projects = client.projects.read_all()
            forms = client.forms.read_all(project_id=projects[0].id)
            instances = client.submissions._read_all_request(
                project_id=projects[0].id, form_id=forms[3].xmlFormId
            )
            print(instances)
