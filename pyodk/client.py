from pyodk import config
from pyodk.endpoints.auth import AuthService
from pyodk.endpoints.project import ProjectService
from pyodk.session import ClientSession


class Client:
    def __init__(self) -> None:
        self.config = config.read_config()
        self.session: ClientSession = ClientSession(
            base_url=self.config["central"]["base_url"]
        )
        self.auth: AuthService = AuthService(session=self.session)
        self.project: ProjectService = ProjectService(
            session=self.session,
            default_project_id=self.config["central"].get("default_project_id"),
        )

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
