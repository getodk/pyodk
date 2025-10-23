from logging import Logger
from pathlib import Path
from string import Formatter
from typing import Any
from urllib.parse import quote, urljoin
from uuid import uuid4

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
    Makes a valid URL by sending each format input field through urllib.parse.quote.

    To parse/un-parse URLs, currently (v2023.5) Central uses JS default functions
    encodeURIComponent and decodeURIComponent, which comply with RFC2396. The more recent
    RFC3986 reserves hex characters 2A (asterisk), 27 (single quote), 28 (left
    parenthesis), and 29 (right parenthesis). Python 3.7+ urllib.parse complies with
    RFC3986 so in order for pyODK to behave as Central expects, these additional 4
    characters are specified as "safe" in `format_field()` to not percent-encode them.

    Currently (v2023.5) Central primarily supports the default submission instanceID
    format per the XForm spec, namely "uuid:" followed by the 36 character UUID string.
    In many endpoints, custom UUIDs (including non-ASCII/UTF-8 chars) will work, but in
    some places they won't. For example the Central page for viewing submission details
    fails on the Submissions OData call, because the OData function to filter by ID
    (`Submission('instanceId')`) only works for the default instanceID format.
    """

    def format_field(self, value: Any, format_spec: str) -> Any:
        return format(quote(str(value), safe="*'()"), format_spec)


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
                allowed_methods=("GET", "PUT", "POST", "DELETE"),
            )
        if (blocksize := kwargs.get("blocksize")) is not None:
            self.blocksize = blocksize
            del kwargs["blocksize"]
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        if kwargs.get("blocksize") is None and hasattr(self, "blocksize"):
            kwargs["blocksize"] = self.blocksize
        super().init_poolmanager(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None and hasattr(self, "timeout"):
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


class Auth(AuthBase):
    def __init__(
        self, session: "Session", username: str, password: str, cache_path: str | Path
    ):
        self.session: Session = session
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
        cache_path: str | Path | None = None,
        chunk_size: int = 16384,
    ) -> None:
        """
        :param base_url: Scheme/domain/port parts of the URL e.g. https://www.example.com
        :param api_version: The Central API version (first part of the URL path).
        :param username: The Central user name to log in with.
        :param password: The Central user's password to log in with.
        :param cache_path: Where to read/write pyodk_cache.toml. If None, the auth
          session is stored only in memory in the "Authorization" session header.
        :param chunk_size: In bytes. For transferring large files (e.g. >1MB), it may be
          noticeably faster to use larger chunks than the default 16384 bytes (16KB).
        """
        super().__init__()
        self.base_url: str = self.base_url_validate(
            base_url=base_url, api_version=api_version
        )
        self.blocksize: int = chunk_size
        self.mount("https://", Adapter(timeout=30, blocksize=self.blocksize))
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
        response = self.request(*args, method=method, url=url, **kwargs)
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

    @staticmethod
    def get_xform_uuid() -> str:
        """
        Get XForm UUID, which is "uuid:" followed by a random uuid v4.
        """
        return f"uuid:{uuid4()}"
