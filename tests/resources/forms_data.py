from datetime import datetime, timezone
from pathlib import Path

test_forms = {
    "project_id": 8,
    "response_data": [
        {
            "projectId": 8,
            "xmlFormId": "dash-in-last-saved",
            "state": "open",
            "enketoId": "48Yd04BkdsshBUeux3m2y4Eea0KbYqB",
            "enketoOnceId": None,
            "createdAt": "2021-04-23T03:03:27.444Z",
            "updatedAt": None,
            "keyId": None,
            "version": "",
            "hash": "4401f8a5781f3c832b70023fb79442a1",
            "sha": "f116369d91b7f356e9d8b75dfd496ecaafa23c92",
            "sha256": "ae91ed9896bcc3a4ea13b52c9727d106634b6b17423b762d3e033f0989e7c1a3",
            "draftToken": "z2umc57Qpt0eZR8wngV9CjzhuEWtLvUttHng$qq6WZt0eptQqOKVMkYPPDStElzF",
            "publishedAt": None,
            "name": "dash-in-last-saved",
        },
        {
            "projectId": 8,
            "xmlFormId": "external_52k",
            "state": "open",
            "enketoId": None,
            "enketoOnceId": "0510ccec266c8e0c88e939c2597341e523535b0e18460fca7c8b4585826a157d",
            "createdAt": "2021-10-28T19:11:37.064Z",
            "updatedAt": "2021-10-28T19:11:59.047Z",
            "keyId": None,
            "version": "1",
            "hash": "31a52959d89621f995fd95b3822e54fd",
            "sha": "e8a128bbfaceb7265f12b903648f6f63700630aa",
            "sha256": "1c5ffdf837c153672fbd7858753c6fa41a8e5813423932e53162016139f11ca1",
            "draftToken": None,
            "publishedAt": "2021-10-28T19:11:57.082Z",
            "name": None,
        },
        {
            "projectId": 8,
            "xmlFormId": "Infos_registre_CTC_20210226",
            "state": "open",
            "enketoId": "fcH3ZtJxHEA5bHBRfp5eq3jBGjeEgbv",
            "enketoOnceId": "293dfdb6fcc501e0e323a8f5d27eb158f6f09b0885b32075a02d75bfdc8703e7",
            "createdAt": "2021-05-18T03:26:25.679Z",
            "updatedAt": "2021-05-18T03:29:23.487Z",
            "keyId": None,
            "version": "04052021",
            "hash": "ca51a72cc206f6557198ae92cb11f7a8",
            "sha": "b98783f9de7a20ff683842701aa897bbe108f933",
            "sha256": "eb8c7e52b4d685f0f8f1bb61fd5957f09ba0fdd26f6b87643cfcdd60389f842f",
            "draftToken": None,
            "publishedAt": "2021-05-18T03:29:23.487Z",
            "name": "Infos registre CTC/CTU",
        },
        {
            "projectId": 8,
            "xmlFormId": "range",
            "state": "open",
            "enketoId": "sRgCcrzoEYKc66geY9fC5vL28bmqFBJ",
            "enketoOnceId": "4e1f9feaa813149c67a8a4c709117f128e4d26153d9061fe70d9b1c5ca7215a6",
            "createdAt": "2021-04-20T21:11:50.794Z",
            "updatedAt": "2021-05-10T20:51:34.202Z",
            "keyId": None,
            "version": "2021042001",
            "hash": "50714e468ceb8a53e4294becc1bfc92a",
            "sha": "0c934f081e3236c2d2e21100ca05bb770885cdf3",
            "sha256": "cc1f15261da182655a77e2005798110ab95897f5d336ef77b60906320317bb30",
            "draftToken": None,
            "publishedAt": "2021-05-10T20:51:22.100Z",
            "name": "range",
        },
    ],
}


def get_xml__range_draft(
    form_id: str | None = "range_draft", version: str | None = None
) -> str:
    if version is None:
        version = datetime.now(timezone.utc).isoformat()
    with open(Path(__file__).parent / "forms" / "range_draft.xml") as fd:
        return fd.read().format(form_id=form_id, version=version)


def get_md__pull_data(version: str | None = None) -> str:
    if version is None:
        version = datetime.now(timezone.utc).isoformat()
    return f"""
    | settings |
    |          | version   |
    |          | {version} |
    | survey |           |            |           |             |
    |        | type      | name       | label     | calculation |
    |        | calculate | fruit      |           | pulldata('fruits', 'name', 'name_key', 'mango') |
    |        | note      | note_fruit | The fruit ${{fruit}} pulled from csv |                      |
    """


md__symbols = """
| settings |
|          | form_title          | form_id       | version |
|          | a non_ascii_form_id | ''=+/*-451%/% | 1       |
| survey |           |            |           |             |
|        | type      | name       | label     | calculation |
|        | calculate | fruit      |           | pulldata('fruits', 'name', 'name_key', 'mango') |
|        | note      | note_fruit | The fruit ${fruit} pulled from csv |                      |
"""
md__dingbat = """
| settings |
|          | form_title  | form_id | version |
|          | ✅          | ✅     | 1       |
| survey |           |            |           |             |
|        | type      | name       | label     | calculation |
|        | calculate | fruit      |           | pulldata('fruits', 'name', 'name_key', 'mango') |
|        | note      | note_fruit | The fruit ${fruit} pulled from csv |                      |
"""
md__upload_file = """
| settings |
|          | form_title  | form_id     | version |
|          | upload_file | upload_file | 1       |
| survey |
|        | type  | name | label |
|        | text  | name | Name  |
|        | file  | file | File  |
"""
