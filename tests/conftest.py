import pytest
from decouple import config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = (
    f"postgresql+psycopg2://{config('PG_USER')}:{config('PG_PASSWORD')}"
    f"@{config('PG_ADDRESS')}:{config('PG_PORT')}/{config('PG_TEST_DB')}"
)

test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    # create_savepoint: app code calling session.commit() only releases/re-opens
    # a SAVEPOINT, so the outer `transaction` below can still roll everything back.
    session = TestSessionLocal(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def make_client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    clients = []

    def _make_client():
        c = TestClient(app)
        clients.append(c)
        return c

    yield _make_client

    app.dependency_overrides.clear()


@pytest.fixture
def client(make_client):
    return make_client()


@pytest.fixture
def mock_caldav(monkeypatch):
    """Patch every caldav_client entry point at its point of use in each router.

    Default: connection succeeds, no calendars, event creation succeeds. Returns
    the MagicMocks so a test can override .return_value or assert on .call_count.
    """
    from unittest.mock import MagicMock

    mocks = {
        "test_connection": MagicMock(return_value=True),
        "get_user_calendars": MagicMock(return_value=[]),
        "create_event": MagicMock(return_value=True),
    }
    monkeypatch.setattr("app.routers.nextcloud_account.test_connection", mocks["test_connection"])
    monkeypatch.setattr("app.routers.event_templates.get_user_calendars", mocks["get_user_calendars"])
    monkeypatch.setattr("app.routers.events.create_event", mocks["create_event"])
    return mocks


def register(client: TestClient, username: str, password: str = "testpass123") -> None:
    """Registers a user; the app logs them in immediately, so `client`'s
    cookie jar now holds a valid session for this user."""
    response = client.post(
        "/users/register",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    assert response.status_code == 200


def connect_nextcloud_account(client: TestClient, username: str = "ncuser", password: str = "ncpass") -> None:
    response = client.post(
        "/nextcloud-account",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
    assert response.status_code == 200, response.text
