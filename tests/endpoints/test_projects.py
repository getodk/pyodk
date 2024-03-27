from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyodk._endpoints.form_assignments import FormAssignmentService
from pyodk._endpoints.project_app_users import ProjectAppUser, ProjectAppUserService
from pyodk._endpoints.projects import Project
from pyodk.client import Client
from requests import Session

from tests.resources import CONFIG_DATA, projects_data

PROJECT_APP_USERS = [
    ProjectAppUser(**d) for d in projects_data.project_app_users["response_data"]
]


@dataclass
class MockContext:
    fa_assign: MagicMock
    pau_list: MagicMock
    pau_create: MagicMock


def get_mock_context(func) -> Callable:
    """
    Inject a context object with mocks for testing projects.

    To use, add a keyword argument "ctx" to the decorated function.
    """

    @wraps(func)
    def patched(*args, **kwargs):
        with (
            patch.object(FormAssignmentService, "assign", return_value=True) as fa_assign,
            patch.object(
                ProjectAppUserService, "list", return_value=PROJECT_APP_USERS
            ) as pau_list,
            patch.object(
                ProjectAppUserService, "create", return_value=True
            ) as pau_create,
        ):
            ctx = MockContext(
                fa_assign=fa_assign,
                pau_list=pau_list,
                pau_create=pau_create,
            )
            kwargs.update({"ctx": ctx})
            return func(*args, **kwargs)

    return patched


@patch("pyodk._utils.session.Auth.login", MagicMock())
@patch("pyodk._utils.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestProjects(TestCase):
    """Tests for `client.project`."""

    def test_list__ok(self):
        """Should return a list of ProjectType objects."""
        fixture = projects_data.test_projects
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"]
            client = Client()
            observed = client.projects.list()
        self.assertEqual(2, len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, Project)

    def test_get__ok(self):
        """Should return a ProjectType object."""
        fixture = projects_data.test_projects
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"][0]
            client = Client()
            # Specify project
            observed = client.projects.get(project_id=fixture["response_data"][0]["id"])
            self.assertIsInstance(observed, Project)
            # Use default
            observed = client.projects.get()
            self.assertIsInstance(observed, Project)


@patch("pyodk._utils.session.Auth.login", MagicMock())
@patch("pyodk._utils.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestProjectCreateAppUsers(TestCase):
    """Test for `client.project.create_app_users`."""

    @get_mock_context
    def test_names_only__list_create__no_existing_users(self, ctx: MockContext):
        """Should call pau.list, pau.create, not fa.assign (no forms specified)."""
        client = Client()
        unames = [u.displayName for u in PROJECT_APP_USERS]
        ctx.pau_list.return_value = []
        ctx.pau_create.return_value = PROJECT_APP_USERS[1]
        client.projects.create_app_users(display_names=unames)
        ctx.pau_list.assert_called_once_with(project_id=None)
        self.assertEqual(2, ctx.pau_create.call_count)
        ctx.pau_create.assert_any_call(display_name=unames[0], project_id=None)
        ctx.pau_create.assert_any_call(display_name=unames[1], project_id=None)
        ctx.fa_assign.assert_not_called()

    @get_mock_context
    def test_names_only__list_create__existing_user(self, ctx: MockContext):
        """Should call pau.create only for the user that doesn't exist."""
        client = Client()
        unames = [u.displayName for u in PROJECT_APP_USERS]
        client.projects.create_app_users(display_names=unames)
        ctx.pau_create.assert_called_once_with(display_name=unames[1], project_id=None)

    @get_mock_context
    def test_names_forms__list_create_assign(self, ctx: MockContext):
        """Should call pau.list, pau.create, fa.assign."""
        client = Client()
        unames = [u.displayName for u in PROJECT_APP_USERS]
        new_user = PROJECT_APP_USERS[1]
        forms = ["form1", "form2"]
        ctx.pau_create.return_value = new_user
        client.projects.create_app_users(display_names=unames, forms=forms)
        ctx.pau_list.assert_called_once_with(project_id=None)
        ctx.pau_create.assert_called_once_with(display_name=unames[1], project_id=None)
        self.assertEqual(2, ctx.fa_assign.call_count)
        ctx.fa_assign.assert_any_call(
            role_id=2,
            user_id=new_user.id,
            form_id=forms[0],
            project_id=None,
        )
        ctx.fa_assign.assert_any_call(
            role_id=2,
            user_id=new_user.id,
            form_id=forms[1],
            project_id=None,
        )


@patch("pyodk._utils.session.Auth.login", MagicMock())
@patch("pyodk._utils.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestProjectAppUsers(TestCase):
    def test_list__ok(self):
        """Should return a list of ProjectAppUser objects."""
        fixture = projects_data.project_app_users
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"]
            client = Client()
            observed = ProjectAppUserService(session=client.session).list(project_id=1)
        self.assertEqual(2, len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, ProjectAppUser)

    def test_create__ok(self):
        """Should return a ProjectAppUser object."""
        fixture = projects_data.project_app_users
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"][0]
            client = Client()
            pau = ProjectAppUserService(session=client.session)
            observed = pau.create(
                display_name=fixture["response_data"][0]["displayName"],
                project_id=fixture["project_id"],
            )
            self.assertIsInstance(observed, ProjectAppUser)
