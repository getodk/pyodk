"""
Mail Merge

This script will use mail merge to create personalized Word documents with
data from Central. In this example, only data from approved submissions
are included.

For a tutorial on how to populate Word templates with Python, see:
https://pbpython.com/python-word-template.html

For more examples, see:
https://github.com/iulica/docx-mailmerge/tree/master/tests

Install requirements for this script in `requirements.txt`. The specified
versions are those that were current when the script was last updated,
though it should work with more recent versions.
Install with `pip install -r requirements.txt`.

To run the script, use `python mail_merge.py`.
"""

import os
from datetime import datetime

from mailmerge import MailMerge
from pyodk.client import Client

# customize these settings to your environment
PROJECT_ID = 1
FORM_ID = "my_form"
TEMPLATE_DOCUMENT = "template.docx"
OUTPUT_FOLDER = "merged"

with Client(project_id=PROJECT_ID) as client:
    submissions = client.submissions.get_table(form_id=FORM_ID)
    for submission in submissions["value"]:
        # only include approved submissions
        if submission["__system"]["reviewState"] == "approved":
            with MailMerge(TEMPLATE_DOCUMENT) as document:
                coordinates = submission["age_location"]["location"]["coordinates"]
                location = f"{coordinates[1]}, {coordinates[0]}"
                generation_date = datetime.now().strftime("%m-%d-%Y %H:%M:%S.%f")
                document.merge(
                    first_name=submission["first_name"],
                    age=submission["age_location"]["age"],
                    location=location,
                    instance_id=submission["meta"]["instanceID"],
                    submission_date=submission["__system"]["submissionDate"],
                    generation_date=generation_date,
                )
                # warning: choose variables with unique values to prevent overwritten files
                output_path = os.path.join(
                    OUTPUT_FOLDER, f"{submission['first_name']}.docx"
                )
                document.write(output_path)
