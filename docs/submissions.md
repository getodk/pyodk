# Submissions

Submission-related functionality is accessed through `client.submissions`. For example:

```python
from pyodk.client import Client

client = Client()
data = client.forms.get_table()["value"]
```

::: pyodk._endpoints.submissions.SubmissionService