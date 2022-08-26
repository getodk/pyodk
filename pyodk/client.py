from typing import Optional

from pyodk import config
from pyodk.endpoints.auth import AuthService
from pyodk.endpoints.forms import FormService
from pyodk.endpoints.odata import ODataService
from pyodk.endpoints.projects import ProjectService
from pyodk.endpoints.submissions import SubmissionService
from pyodk.session import ClientSession


class Client:
    def __init__(self, project_id: Optional[int] = None) -> None:
        self.config = config.read_config()
        self._project_id: Optional[int] = project_id
        self.session: ClientSession = ClientSession(
            base_url=self.config["central"]["base_url"]
        )
        self.auth: AuthService = AuthService(session=self.session)
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
        self.odata: ODataService = ODataService(
            session=self.session, default_project_id=self.project_id
        )

    @property
    def project_id(self) -> Optional[int]:
        if self._project_id is None:
            return self.config["central"].get("default_project_id")
        else:
            return self._project_id

    @project_id.setter
    def project_id(self, v: str):
        self._project_id = v

    def _login(self):
        token = self.auth.get_token(
            username=self.config["central"]["username"],
            password=self.config["central"]["password"],
        )
        self.session.s.headers["Authorization"] = "Bearer " + token

    def __enter__(self) -> "Client":
        self.session.__enter__()
        self._login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.__exit__(exc_type, exc_val, exc_tb)
