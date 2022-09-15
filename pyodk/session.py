from urllib.parse import urljoin

from requests import Response
from requests import Session as RequestsSession
from requests.adapters import HTTPAdapter, Retry

from pyodk.errors import PyODKError


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


class Session(RequestsSession):
    def __init__(self, base_url: str, api_version: str) -> None:
        super().__init__()
        self.base_url: str = self.base_url_validate(
            base_url=base_url, api_version=api_version
        )
        self.mount_pyodk_adapter()

    @staticmethod
    def base_url_validate(base_url: str, api_version: str):
        if not base_url.endswith(f"{api_version}/"):
            if base_url.endswith(api_version):
                base_url = base_url + "/"
            elif not base_url.endswith(api_version):
                base_url = base_url.rstrip("/") + f"/{api_version}/"
        return base_url

    def mount_pyodk_adapter(self):
        self.mount("https://", PyODKAdapter(timeout=30))

    def urljoin(self, url: str) -> str:
        return urljoin(self.base_url, url.lstrip("/"))

    def request(self, method, url, *args, **kwargs):
        return super().request(method, self.urljoin(url), *args, **kwargs)

    def prepare_request(self, request):
        request.url = self.urljoin(request.url)
        return super().prepare_request(request)

    def get_200_or_error(self, url, logger, *args, **kwargs) -> Response:
        response = self.request("GET", url, *args, **kwargs)
        if response.status_code == 200:
            return response
        else:
            msg = (
                f"The request to {url} failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            err = PyODKError(msg, response)
            logger.error(err, exc_info=True)
            raise err
