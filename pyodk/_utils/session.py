from logging import Logger
from string import Formatter
from typing import Any
from urllib.parse import quote_plus, urljoin

from requests import PreparedRequest, Response
from requests import Session as RequestsSession
from requests.adapters import HTTPAdapter, Retry
from requests.auth import AuthBase
from requests.exceptions import HTTPError

from pyodk.__version__ import __version__
from pyodk._endpoints.auth import AuthService
from pyodk.errors import PyODKError


class URLFormatter(Formatter):
    """
    Makes a valid URL by sending each format input field through urllib.parse.quote_plus.
    """

    def format_field(self, value: Any, format_spec: str) -> Any:
        return format(quote_plus(str(value)), format_spec)


_URL_FORMATTER = URLFormatter()


class Adapter(HTTPAdapter):
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


class Auth(AuthBase):
    def __init__(self, session: "Session", username: str, password: str, cache_path: str):
        self.session: "Session" = session
        self.username: str = username
        self.password: str = password
        self.service: AuthService = AuthService(session=session, cache_path=cache_path)
        self._skip_auth_check: bool = False

    def login(self) -> str:
        """
        Log in to Central (create new session or verify existing).

        :return: Bearer <token>
        """
        if "Authorization" not in self.session.headers:
            try:
                self._skip_auth_check = True  # Avoid loop of death due to the below call.
                t = self.service.get_token(username=self.username, password=self.password)
                self.session.headers["Authorization"] = "Bearer " + t
            finally:
                self._skip_auth_check = False
        return self.session.headers["Authorization"]

    def __call__(self, r: PreparedRequest, *args, **kwargs):
        if "Authorization" not in r.headers and not self._skip_auth_check:
            r.headers["Authorization"] = self.login()
        return r


class Session(RequestsSession):
    def __init__(
        self,
        base_url: str,
        api_version: str,
        username: str,
        password: str,
        cache_path: str,
    ) -> None:
        """
        :param base_url: Scheme/domain/port parts of the URL e.g. https://www.example.com
        :param api_version: The Central API version (first part of the URL path).
        :param username: The Central user name to log in with.
        :param password: The Central user's password to log in with.
        :param cache_path: Where to read/write pyodk_cache.toml.
        """
        super().__init__()
        self.base_url: str = self.base_url_validate(
            base_url=base_url, api_version=api_version
        )
        self.mount("https://", Adapter(timeout=30))
        self.headers.update({"User-Agent": f"pyodk v{__version__}"})
        self.auth: Auth = Auth(
            session=self, username=username, password=password, cache_path=cache_path
        )

    @staticmethod
    def base_url_validate(base_url: str, api_version: str):
        if not base_url.endswith(f"{api_version}/"):
            if base_url.endswith(api_version):
                base_url = base_url + "/"
            elif not base_url.endswith(api_version):
                base_url = base_url.rstrip("/") + f"/{api_version}/"
        return base_url

    def urljoin(self, url: str) -> str:
        return urljoin(self.base_url, url.lstrip("/"))

    @staticmethod
    def urlformat(url: str, *args, **kwargs) -> str:
        return _URL_FORMATTER.format(url, *args, **kwargs)

    @staticmethod
    def urlquote(url: str) -> str:
        return _URL_FORMATTER.format_field(url, format_spec="")

    def request(self, method, url, *args, **kwargs):
        return super().request(method, self.urljoin(url), *args, **kwargs)

    def prepare_request(self, request):
        request.url = self.urljoin(request.url)
        return super().prepare_request(request)

    def response_or_error(
        self, method: str, url: str, logger: Logger, *args, **kwargs
    ) -> Response:
        response = self.request(method=method, url=url, *args, **kwargs)
        try:
            response.raise_for_status()
        except HTTPError as e:
            msg = (
                f"The request to {self.urljoin(url)} failed."
                f" Status: {response.status_code}, content: {response.text}"
            )
            err = PyODKError(msg, response)
            logger.error(err, exc_info=True)
            raise err from e
        else:
            return response
