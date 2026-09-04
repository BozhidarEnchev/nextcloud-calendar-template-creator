from app.models.nextcloud_account import NextcloudAccount
from tests.conftest import connect_nextcloud_account, register

def test_get_nextcloud_account_page_with_no_connected_account(client):
    register(client, "testuser", "testpassword")
    response = client.get("/nextcloud-account")
    assert response.status_code == 200
    assert "No Nextcloud account connected yet." in response.text


def test_get_nextcloud_account_page_with_connected_account(client):
    register(client, "testuser", "testpassword")
    connect_nextcloud_account(client, "ncuser", "ncpass")
    response = client.get("/nextcloud-account")
    assert response.status_code == 200


def test_get_nextcloud_account_page_with_no_registered_user(client):
    response = client.get("/nextcloud-account", follow_redirects=False)
    assert response.status_code == 303


def test_delete_nextcloud_account(client, db_session):
    register(client, "testuser", "testpassword")
    connect_nextcloud_account(client, "ncuser", "ncpass")
    response = client.post("/nextcloud-account/delete", follow_redirects=True)
    assert response.status_code == 200
    response = client.get("/nextcloud-account", follow_redirects=False)
    assert "No Nextcloud account connected yet." in response.text
    accounts = db_session.query(NextcloudAccount).all()
    assert len(accounts) == 0


def test_update_nextcloud_account(client, db_session):
    register(client, "testuser", "testpassword")
    connect_nextcloud_account(client, "ncuser", "ncpass")

    original = db_session.query(NextcloudAccount).one()
    original_id = original.id
    original_encrypted_password = original.encrypted_password

    response = client.post(
        "/nextcloud-account",
        data={"username": "newuser", "password": "newpass"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    accounts = db_session.query(NextcloudAccount).all()
    assert len(accounts) == 1
    assert accounts[0].id == original_id
    assert accounts[0].username == "newuser"
    assert accounts[0].encrypted_password != original_encrypted_password


def test_connection_test_with_no_account(client, mock_caldav):
    register(client, "testuser", "testpassword")
    response = client.get("/nextcloud-account/test")
    assert response.status_code == 200
    assert "No Nextcloud account connected yet." in response.text
    mock_caldav["test_connection"].assert_not_called()


def test_connection_test_success(client, mock_caldav):
    register(client, "testuser", "testpassword")
    connect_nextcloud_account(client, "ncuser", "ncpass")
    response = client.get("/nextcloud-account/test")
    assert response.status_code == 200
    assert "Connection successful." in response.text


def test_connection_test_failure(client, mock_caldav):
    mock_caldav["test_connection"].return_value = False
    register(client, "testuser", "testpassword")
    connect_nextcloud_account(client, "ncuser", "ncpass")
    response = client.get("/nextcloud-account/test")
    assert response.status_code == 200
    assert "Could not connect" in response.text
