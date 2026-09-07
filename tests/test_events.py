from datetime import date

from sqlalchemy import select

from app.models.event_template import EventTemplate
from app.models.event_template_item import EventTemplateItem
from tests.conftest import connect_nextcloud_account, register


def _create_template_with_item(client, db_session, template_name="Work day", item_title="Bus to work"):
    client.post("/event-templates/new", data={"name": template_name})
    template = db_session.scalars(select(EventTemplate).where(EventTemplate.name == template_name)).one()
    resp = client.post(
        f"/event-templates/{template.id}/items",
        data={
            "title": item_title,
            "start_time": "08:00",
            "end_time": "08:30",
            "calendar_url": "http://example/cal",
            "location": "",
            "description": "",
        },
    )
    assert resp.status_code == 200, resp.text
    return template


def test_events_create_requires_nextcloud_account(client, db_session):
    register(client, "testuser")
    template = _create_template_with_item(client, db_session)

    resp = client.post("/events", data={"template_id": template.id, "event_date": "2026-09-01"})
    assert resp.status_code == 403


def test_events_create_rejects_template_with_no_items(client, db_session, mock_caldav):
    register(client, "testuser")
    connect_nextcloud_account(client)
    client.post("/event-templates/new", data={"name": "Empty template"})
    template = db_session.scalars(select(EventTemplate).where(EventTemplate.name == "Empty template")).one()

    resp = client.post("/events", data={"template_id": template.id, "event_date": "2026-09-01"})
    assert resp.status_code == 400
    mock_caldav["create_event"].assert_not_called()


def test_events_create_success(client, db_session, mock_caldav):
    register(client, "testuser")
    connect_nextcloud_account(client)
    template = _create_template_with_item(client, db_session)

    resp = client.post("/events", data={"template_id": template.id, "event_date": "2026-09-01"})
    assert resp.status_code == 200
    assert "Created" in resp.text
    assert "Failed" not in resp.text
    mock_caldav["create_event"].assert_called_once()


def test_events_create_reports_per_item_failure(client, db_session, mock_caldav):
    register(client, "testuser")
    connect_nextcloud_account(client)
    template = _create_template_with_item(client, db_session, item_title="Bus to work")
    client.post(
        f"/event-templates/{template.id}/items",
        data={
            "title": "Work",
            "start_time": "09:00",
            "end_time": "17:00",
            "calendar_url": "http://example/cal2",
            "location": "",
            "description": "",
        },
    )

    # first item's create_event call succeeds, second one fails
    mock_caldav["create_event"].side_effect = [True, False]

    resp = client.post("/events", data={"template_id": template.id, "event_date": "2026-09-01"})
    assert resp.status_code == 200
    assert "Created" in resp.text
    assert "Failed" in resp.text


def test_events_create_passes_correct_arguments_to_create_event(client, db_session, mock_caldav):
    register(client, "testuser")
    connect_nextcloud_account(client, "ncuser", "ncpass")
    template = _create_template_with_item(client, db_session)
    item = db_session.scalars(select(EventTemplateItem).where(EventTemplateItem.template_id == template.id)).one()

    client.post("/events", data={"template_id": template.id, "event_date": "2026-09-01"})

    mock_caldav["create_event"].assert_called_once()
    _, kwargs = mock_caldav["create_event"].call_args
    assert kwargs["caldav_user"] == "ncuser"
    assert kwargs["item"] is item
    assert kwargs["event_date"] == date(2026, 9, 1)
