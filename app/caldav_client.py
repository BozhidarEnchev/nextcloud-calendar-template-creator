from datetime import UTC, date, datetime
from uuid import uuid4

import caldav
from decouple import config
from icalendar import Calendar as ICalendar
from icalendar import Event as ICalEvent

from app.models.event_template_item import EventTemplateItem
from app.security import decrypt_secret

SERVER_URL = config("SERVER_URL")

def build_client(caldav_user: str, app_pasword: bytes) -> caldav.DAVClient:
    caldav_url = f"{SERVER_URL}/remote.php/dav/principals/users/{caldav_user}"
    return caldav.DAVClient(url=caldav_url, username=caldav_user, password=decrypt_secret(app_pasword))


def test_connection(caldav_user: str, app_pasword: bytes) -> bool:
    client = build_client(caldav_user, app_pasword)
    try:
        client.principal()
    except Exception:
        return False
    return True


def get_user_calendars(caldav_user: str, app_pasword: bytes) -> list[caldav.collection.Calendar] | False:
    client = build_client(caldav_user, app_pasword)
    try:
        principal = client.principal()
    except Exception:
        return False
    return principal.calendars()


def create_event(caldav_user: str, app_pasword: bytes, item: EventTemplateItem, event_date: date) -> bool:
    client = build_client(caldav_user, app_pasword)

    try:
        calendar = client.calendar(url=item.calendar_url)

        vevent = ICalEvent()
        vevent.add("uid", str(uuid4()))
        vevent.add("dtstamp", datetime.now(UTC))
        vevent.add("summary", item.title)
        vevent.add("dtstart", datetime.combine(event_date, item.start_time))
        vevent.add("dtend", datetime.combine(event_date, item.end_time))
        if item.description:
            vevent.add("description", item.description)
        if item.location:
            vevent.add("location", item.location)

        ical = ICalendar()
        ical.add("prodid", "-//Calendar Event Template Creator//")
        ical.add("version", "2.0")
        ical.add_component(vevent)

        calendar.save_event(ical.to_ical().decode("utf-8"))
    except Exception:
        return False
    return True
