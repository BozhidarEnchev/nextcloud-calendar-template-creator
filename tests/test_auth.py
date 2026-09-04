from tests.conftest import register


def test_register_new_user_can_access_index(client):
    register(client, "newuser")
    resp = client.get("/")

    assert resp.status_code == 200


def test_forbid_register_when_user_is_taken(client):
    register(client, "user1", "123456")
    resp = client.post(
        "/users/register",
        data={"username": "user1", "password": "pass123"},
        follow_redirects=False,
    )

    assert resp.status_code == 400


def test_login_with_correct_credentials(client):
    register(client, "newuser", "pass123")
    resp = client.post(
        "/users/login",
        data={"username": "newuser", "password": "pass123"},
        follow_redirects=False,
    )

    assert resp.status_code == 303


def test_login_with_incorrect_credentials(client):
    register(client, "user", "pass123")
    resp = client.post(
        "/users/login",
        data={"username": "user", "password": "123456"},
        follow_redirects=False,
    )

    assert resp.status_code == 400


def test_login_with_nonexistent_user(client):
    resp = client.post(
        "/users/login",
        data={"username": "nonexistent", "password": "123456"},
        follow_redirects=False,
    )

    assert resp.status_code == 400


def test_logout(client):
    register(client, "user", "pass123")
    resp = client.post(
        "/users/logout",
        follow_redirects=False,
    )
    assert resp.status_code == 303
