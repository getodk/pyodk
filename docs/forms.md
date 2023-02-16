# Forms

Form-related functionality is accessed through `client.forms`. For example:

```python
from pyodk.client import Client

client = Client()
forms = client.forms.list()
```

::: pyodk._endpoints.forms.FormService