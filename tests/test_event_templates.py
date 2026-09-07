from datetime import time
from types import SimpleNamespace

from sqlalchemy import select

from app.models.event_template import EventTemplate
from app.models.event_template_item import EventTemplateItem
from app.models.user import User
from tests.conftest import connect_nextcloud_account, register


def _get_template(db_session, name: str) -> EventTemplate:
    return db_session.scalars(select(EventTemplate).where(EventTemplate.name == name)).one()


def _add_item(client, template_id: int, **overrides) -> None:
    data = {
        "title": "Bus to work",
        "start_time": "08:00",
        "end_time": "08:30",
        "calendar_url": "http://example/cal",
        "location": "",
        "description": "",
    }
    data.update(overrides)
    resp = client.post(f"/event-templates/{template_id}/items", data=data)
    assert resp.status_code == 200, resp.text


def test_create_template(client, db_session):
    register(client, "testuser")

    resp = client.post("/event-templates/new", data={"name": "Work day"}, follow_redirects=False)
    assert resp.status_code == 303

    template = _get_template(db_session, "Work day")
    user = db_session.scalars(select(User).where(User.username == "testuser")).one()
    assert template.user_id == user.id


def test_edit_template_requires_nextcloud_account(client, db_session):
    register(client, "testuser")
    client.post("/event-templates/new", data={"name": "Work day"})
    template = _get_template(db_session, "Work day")

    resp = client.get(f"/event-templates/{template.id}")
    assert resp.status_code == 403


def test_edit_template_shows_available_calendars(client, db_session, mock_caldav):
    register(client, "testuser")
    connect_nextcloud_account(client)
    client.post("/event-templates/new", data={"name": "Work day"})
    template = _get_template(db_session, "Work day")

    mock_caldav["get_user_calendars"].return_value = [
        SimpleNamespace(url="http://example/cal/personal", name="Personal"),
    ]

    resp = client.get(f"/event-templates/{template.id}")
    assert resp.status_code == 200
    assert "Personal" in resp.text


def test_update_template_name(client, db_session):
    register(client, "testuser")
    client.post("/event-templates/new", data={"name": "Old name"})
    template = _get_template(db_session, "Old name")

    resp = client.post(f"/event-templates/{template.id}", data={"name": "New name"}, follow_redirects=False)
    assert resp.status_code == 303

    db_session.refresh(template)
    assert template.name == "New name"


def test_update_template_blank_name_keeps_existing_name(client, db_session):
    register(client, "testuser")
    client.post("/event-templates/new", data={"name": "Keep me"})
    template = _get_template(db_session, "Keep me")

    resp = client.post(f"/event-templates/{template.id}", data={"name": ""}, follow_redirects=False)
    assert resp.status_code == 303

    db_session.refresh(template)
    assert template.name == "Keep me"


def test_add_item_to_template(client, db_session):
    register(client, "testuser")
    client.post("/event-templates/new", data={"name": "Work day"})
    template = _get_template(db_session, "Work day")

    _add_item(
        client,
        template.id,
        title="Bus to work",
        start_time="08:00",
        end_time="08:30",
        calendar_url="http://example/cal",
        location="Main St",
        description="Morning commute",
    )

    item = db_session.scalars(select(EventTemplateItem).where(EventTemplateItem.template_id == template.id)).one()
    assert item.title == "Bus to work"
    assert item.start_time == time(8, 0)
    assert item.end_time == time(8, 30)
    assert item.calendar_url == "http://example/cal"
    assert item.location == "Main St"
    assert item.description == "Morning commute"


def test_add_item_to_nonexistent_template(client):
    register(client, "testuser")

    resp = client.post(
        "/event-templates/999999/items",
        data={
            "title": "x",
            "start_time": "08:00",
            "end_time": "08:30",
            "calendar_url": "http://example/cal",
            "location": "",
            "description": "",
        },
    )
    assert resp.status_code == 404


def test_delete_item(client, db_session):
    register(client, "testuser")
    client.post("/event-templates/new", data={"name": "Work day"})
    template = _get_template(db_session, "Work day")
    _add_item(client, template.id)
    item = db_session.scalars(select(EventTemplateItem).where(EventTemplateItem.template_id == template.id)).one()

    resp = client.delete(f"/event-templates/{template.id}/items/{item.id}")
    assert resp.status_code == 200

    assert db_session.scalar(select(EventTemplateItem).where(EventTemplateItem.id == item.id)) is None


def test_delete_template_cascades_items(client, db_session):
    register(client, "testuser")
    client.post("/event-templates/new", data={"name": "Work day"})
    template = _get_template(db_session, "Work day")
    _add_item(client, template.id)
    item = db_session.scalars(select(EventTemplateItem).where(EventTemplateItem.template_id == template.id)).one()
    template_id, item_id = template.id, item.id

    resp = client.delete(f"/event-templates/{template_id}", follow_redirects=False)
    assert resp.status_code == 303
    assert db_session.scalar(select(EventTemplate).where(EventTemplate.id == template_id)) is None
    assert db_session.scalar(select(EventTemplateItem).where(EventTemplateItem.id == item_id)) is None
