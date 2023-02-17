# HTTP verb methods

For interacting with parts of the ODK Central API ([docs](https://odkcentral.docs.apiary.io)) that have not been implemented in `pyodk`, use HTTP verb methods exposed on the `Client`:

```python
client.get("projects/8")
client.post("projects/7/app-users", json={"displayName": "Lab Tech"})
```

These methods provide convenient access to `Client.session`, which is a [`requests.Session`](https://requests.readthedocs.io/en/latest/user/advanced/#session-objects) object subclass. The `Session` has customised to prefix request URLs with the `base_url` from the pyodk config. For example with a base_url `https://www.example.com`, a call to `client.session.get("projects/8")` gets the details of `project_id=8`, using the full url `https://www.example.com/v1/projects/8`.

Learn more in [this example](/examples/beyond-library-methods/).