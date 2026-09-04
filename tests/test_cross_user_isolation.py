from app.models.event_template import EventTemplate
from app.models.event_template_item import EventTemplateItem
from tests.conftest import connect_nextcloud_account, register


def _create_template(client, name="Owner's template") -> None:
    resp = client.post("/event-templates/new", data={"name": name}, follow_redirects=True)
    assert resp.status_code == 200


def _template_id(db_session, name: str) -> int:
    template = db_session.query(EventTemplate).filter(EventTemplate.name == name).one()
    return template.id


def _create_item(client, template_id: int, title="Bus to work") -> None:
    resp = client.post(
        f"/event-templates/{template_id}/items",
        data={
            "title": title,
            "start_time": "08:00",
            "end_time": "08:30",
            "calendar_url": "http://example/cal",
            "location": "",
            "description": "",
        },
    )
    assert resp.status_code == 200, resp.text


def test_template_list_only_shows_own_templates(make_client, db_session, mock_caldav):
    owner = make_client()
    register(owner, "listowner")
    _create_template(owner, "Owner-only template")

    other = make_client()
    register(other, "listother")

    resp = other.get("/event-templates")
    assert resp.status_code == 200
    assert "Owner-only template" not in resp.text


def test_template_edit_blocks_non_owner(make_client, db_session, mock_caldav):
    owner = make_client()
    register(owner, "edit_owner")
    _create_template(owner, "Edit-target template")
    template_id = _template_id(db_session, "Edit-target template")

    attacker = make_client()
    register(attacker, "edit_attacker")
    connect_nextcloud_account(attacker)  # needed to get past the account-gate and reach ownership check

    resp = attacker.get(f"/event-templates/{template_id}")
    assert resp.status_code == 404
    assert "Template not found" in resp.text


def test_template_update_blocks_non_owner(make_client, db_session, mock_caldav):
    owner = make_client()
    register(owner, "update_owner")
    _create_template(owner, "Update-target template")
    template_id = _template_id(db_session, "Update-target template")

    attacker = make_client()
    register(attacker, "update_attacker")

    resp = attacker.post(f"/event-templates/{template_id}", data={"name": "Hijacked name"})
    assert resp.status_code in (303, 200)  # redirects, doesn't 500

    db_session.refresh(db_session.query(EventTemplate).filter(EventTemplate.id == template_id).one())
    template = db_session.query(EventTemplate).filter(EventTemplate.id == template_id).one()
    assert template.name == "Update-target template"  # unchanged


def test_template_delete_blocks_non_owner(make_client, db_session, mock_caldav):
    owner = make_client()
    register(owner, "delete_owner")
    _create_template(owner, "Delete-target template")
    template_id = _template_id(db_session, "Delete-target template")

    attacker = make_client()
    register(attacker, "delete_attacker")

    resp = attacker.delete(f"/event-templates/{template_id}")
    assert resp.status_code == 404

    still_there = db_session.query(EventTemplate).filter(EventTemplate.id == template_id).one_or_none()
    assert still_there is not None


def test_item_create_blocks_non_owner(make_client, db_session, mock_caldav):
    owner = make_client()
    register(owner, "itemcreate_owner")
    _create_template(owner, "Item-create-target template")
    template_id = _template_id(db_session, "Item-create-target template")

    attacker = make_client()
    register(attacker, "itemcreate_attacker")

    resp = attacker.post(
        f"/event-templates/{template_id}/items",
        data={
            "title": "Injected item",
            "start_time": "08:00",
            "end_time": "08:30",
            "calendar_url": "http://example/cal",
            "location": "",
            "description": "",
        },
    )
    assert resp.status_code == 404

    items = db_session.query(EventTemplateItem).filter(EventTemplateItem.template_id == template_id).all()
    assert items == []


def test_item_delete_blocks_non_owner(make_client, db_session, mock_caldav):
    owner = make_client()
    register(owner, "itemdelete_owner")
    _create_template(owner, "Item-delete-target template")
    template_id = _template_id(db_session, "Item-delete-target template")
    _create_item(owner, template_id)
    item = db_session.query(EventTemplateItem).filter(EventTemplateItem.template_id == template_id).one()

    attacker = make_client()
    register(attacker, "itemdelete_attacker")

    resp = attacker.delete(f"/event-templates/{template_id}/items/{item.id}")
    assert resp.status_code == 404

    still_there = db_session.query(EventTemplateItem).filter(EventTemplateItem.id == item.id).one_or_none()
    assert still_there is not None


def test_events_create_blocks_non_owner(make_client, db_session, mock_caldav):
    owner = make_client()
    register(owner, "eventscreate_owner")
    _create_template(owner, "Events-create-target template")
    template_id = _template_id(db_session, "Events-create-target template")
    _create_item(owner, template_id)

    attacker = make_client()
    register(attacker, "eventscreate_attacker")
    connect_nextcloud_account(attacker)  # needed to get past the account-gate and reach ownership check

    resp = attacker.post("/events", data={"template_id": template_id, "event_date": "2026-09-01"})
    assert resp.status_code == 404
    mock_caldav["create_event"].assert_not_called()


def test_nextcloud_account_view_does_not_leak_other_users_account(make_client, mock_caldav):
    owner = make_client()
    register(owner, "nc_owner")
    connect_nextcloud_account(owner, username="owner_nc_username")

    other = make_client()
    register(other, "nc_other")

    resp = other.get("/nextcloud-account")
    assert resp.status_code == 200
    assert "owner_nc_username" not in resp.text
