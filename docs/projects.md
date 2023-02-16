# Projects

Project-related functionality is accessed through `client.projects`. For example:

```python
from pyodk.client import Client

client = Client()
forms = client.projects.list()
```

::: pyodk._endpoints.projects.ProjectService