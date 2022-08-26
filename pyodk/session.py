from typing import Optional

from requests import Session
from requests.adapters import HTTPAdapter, Retry


class PyODKAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        if "max_retries" not in kwargs:
            kwargs["max_retries"] = Retry(
                total=3,
                backoff_factor=2,
                status_forcelist=(429, 500, 502, 503, 504),
                method_whitelist=("GET", "PUT", "POST", "DELETE"),
            )
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None and hasattr(self, "timeout"):
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


class ClientSession:
    def __init__(self, base_url: str) -> None:
        self.base_url: str = base_url
        self.s: Optional[Session] = None

    def __enter__(self) -> Session:
        self.s = Session()
        self.s.mount("https://", PyODKAdapter(timeout=30))
        return self.s

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.s is not None:
            self.s.close()
        self.session = None
