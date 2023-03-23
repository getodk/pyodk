from typing import Callable, Optional

from pyodk._endpoints.comments import CommentService
from pyodk._endpoints.forms import FormService
from pyodk._endpoints.projects import ProjectService
from pyodk._endpoints.submissions import SubmissionService
from pyodk._utils import config
from pyodk._utils.session import Session


class Client:
    """
    A connection to a specific ODK Central server. Manages authentication and provides
    access to Central functionality through methods organized by the Central resource
    they are most related to.

    :param config_path: Where to read the pyodk_config.toml. Defaults to the
        path in PYODK_CONFIG_FILE, then the user home directory.
    :param cache_path: Where to read/write pyodk_cache.toml. Defaults to the
        path in PYODK_CACHE_FILE, then the user home directory.
    :param project_id: The project ID to use for all client calls. Defaults to the
        "default_project_id" in pyodk_config.toml, or can be specified per call.
    :param session: A prepared pyodk.session.Session class instance, or an instance
        of a customised subclass.
    :param api_version: The ODK Central API version, which is used in the URL path
        e.g. 'v1' in 'https://www.example.com/v1/projects'.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        cache_path: Optional[str] = None,
        project_id: Optional[int] = None,
        session: Optional[Session] = None,
        api_version: Optional[str] = "v1",
    ) -> None:
        self.config: config.Config = config.read_config(config_path=config_path)
        self._project_id: Optional[int] = project_id
        if session is None:
            session = Session(
                base_url=self.config.central.base_url,
                api_version=api_version,
                username=self.config.central.username,
                password=self.config.central.password,
                cache_path=cache_path,
            )
        self.session: Session = session

        # Delegate http verbs for ease of use.
        self.get: Callable = self.session.get
        self.post: Callable = self.session.post
        self.put: Callable = self.session.put
        self.patch: Callable = self.session.patch
        self.delete: Callable = self.session.delete

        # Endpoints
        self.projects: ProjectService = ProjectService(
            session=self.session,
            default_project_id=self.project_id,
        )
        self.forms: FormService = FormService(
            session=self.session, default_project_id=self.project_id
        )
        self.submissions: SubmissionService = SubmissionService(
            session=self.session, default_project_id=self.project_id
        )
        self._comments: CommentService = CommentService(
            session=self.session, default_project_id=self.project_id
        )

    @property
    def project_id(self) -> Optional[int]:
        if self._project_id is None:
            return self.config.central.default_project_id
        else:
            return self._project_id

    @project_id.setter
    def project_id(self, v: str):
        self._project_id = v

    def open(self) -> "Client":
        """Enter the session, and authenticate."""
        self.session.__enter__()
        self.session.auth.login()
        return self

    def close(self, *args):
        """Close the session."""
        self.session.__exit__(*args)

    def __enter__(self) -> "Client":
        return self.open()

    def __exit__(self, *args):
        self.close(*args)
