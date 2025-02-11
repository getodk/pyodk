test_submission_attachments = [
    {
        "name": "file1.jpg",
        "exists": True,
    },
    {
        "name": "file2.jpg",
        "exists": False,
    },
    {
        "name": "file3.jpg",
        "exists": True,
    },
]

test_submission_attachment_get = {
    "content": b"Mock binary data for attachment download",
    "file_name": "file1.jpg",
    "instance_id": "uuid:96f2a014-eaa1-466a-abe2-3ccacc756d5a",
    "form_id": "sub_attachments",
    "project_id": 8,
}

test_submission_attachment_upload = {
    "project_id": 8,
    "form_id": "sub_attachments",
    "instance_id": "uuid:96f2a014-eaa1-466a-abe2-3ccacc756d5a",
    "file_path_or_bytes": b"Mock binary data for attachment download",
    "file_name": "file1.jpg",
}
