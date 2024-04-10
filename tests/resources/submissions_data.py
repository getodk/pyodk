test_submissions = {
    "project_id": 8,
    "form_id": "range",
    "response_data": [
        {
            "instanceId": "uuid:96f2a014-eaa1-466a-abe2-3ccacc756d5a",
            "submitterId": 28,
            "deviceId": None,
            "createdAt": "2021-05-10T20:51:51.404Z",
            "updatedAt": None,
            "reviewState": None,
        },
        {
            "instanceId": "uuid:0ef76597-5a6d-4788-b924-d875f615025c",
            "submitterId": 28,
            "deviceId": None,
            "createdAt": "2021-05-10T20:51:48.198Z",
            "updatedAt": None,
            "reviewState": None,
        },
        {
            "instanceId": "uuid:2d434c15-096a-41aa-a9f5-714badf72d0d",
            "submitterId": 28,
            "deviceId": None,
            "createdAt": "2021-05-10T20:51:45.344Z",
            "updatedAt": None,
            "reviewState": None,
        },
        {
            "instanceId": "uuid:4ef8a694-2848-4c77-a0db-31a3b53c14cd",
            "submitterId": 28,
            "deviceId": None,
            "createdAt": "2021-05-10T20:51:40.330Z",
            "updatedAt": None,
            "reviewState": None,
        },
    ],
}
test_xml = """
<data id="my_form" version="v1">
  <meta>
    <instanceID>uuid:85cb9aff-005e-4edd-9739-dc9c1a829c44</instanceID>
  </meta>
  <name>Alice</name>
  <age>36</age>
</data>
"""


def get_xml__fruits(
    form_id: str,
    version: str,
    instance_id: str,
    deprecated_instance_id: str | None = None,
    selected_fruit: str = "Papaya",
) -> str:
    """
    Get Submission XML for the "fruits" form that uses an external data list.

    :param form_id: The xmlFormId of the Form being referenced.
    :param version: The version of the form that the submission is for.
    :param instance_id: The instanceId of the Submission being referenced.
    :param deprecated_instance_id: If the submission is an edit, then the instance_id of
      the submission being replaced must be provided.
    :param selected_fruit: Which delicious tropical fruit do you like?
    """
    iidd = ""
    if deprecated_instance_id is not None:
        iidd = f"<deprecatedID>{deprecated_instance_id}</deprecatedID>"
    return f"""
    <data id="{form_id}" version="{version}">
      <meta>{iidd}
        <instanceID>{instance_id}</instanceID>
      </meta>
      <fruit>{selected_fruit}</fruit>
      <note_fruit/>
    </data>
    """
