test_entities = [
    {
        "uuid": "uuid:85cb9aff-005e-4edd-9739-dc9c1a829c44",
        "createdAt": "2018-01-19T23:58:03.395Z",
        "updatedAt": "2018-03-21T12:45:02.312Z",
        "deletedAt": "2018-03-21T12:45:02.312Z",
        "creatorId": 1,
        "currentVersion": {
            "label": "John (88)",
            "current": True,
            "createdAt": "2018-03-21T12:45:02.312Z",
            "creatorId": 1,
            "userAgent": "Enketo/3.0.4",
            "version": 1,
            "baseVersion": None,
            "conflictingProperties": None,
            "data": {"firstName": "John", "age": "88"},
        },
    },
    {
        "uuid": "uuid:85cb9aff-005e-4edd-9739-dc9c1a829c45",
        "createdAt": "2018-01-19T23:58:03.395Z",
        "updatedAt": "2018-03-21T12:45:02.312Z",
        "deletedAt": "2018-03-21T12:45:02.312Z",
        "creatorId": 1,
        "conflict": "soft",
        "currentVersion": {
            "label": "John (89)",
            "current": True,
            "createdAt": "2018-03-21T12:45:02.312Z",
            "creatorId": 1,
            "userAgent": "Enketo/3.0.4",
            "version": 2,
            "baseVersion": 1,
            "conflictingProperties": None,
            "data": {"firstName": "John", "age": "88"},
        },
    },
]
test_entities_data = {
    "firstName": "John",
    "age": "88",
}
