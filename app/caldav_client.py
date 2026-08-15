from typing import List
from decouple import config
import caldav


SERVER_URL = config("SERVER_URL")

def build_client(caldav_user: str, app_pasword: bytes) -> caldav.DAVClient:
    caldav_url = f"{SERVER_URL}/remote.php/dav/principals/users/{caldav_user}"
    return caldav.DAVClient(url=caldav_url, username=caldav_user, password=app_pasword)


def test_connection(caldav_user: str, app_pasword: bytes) -> bool:
    client = build_client(caldav_user, app_pasword)
    try:
        client.principal()
    except caldav.lib.error.DAVError:
        return False
    except Exception:
        return False
    return True


def get_user_calendars(caldav_user: str, app_pasword: bytes) -> List[caldav.collection.Calendar] | False:
    client = build_client(caldav_user, app_pasword)
    try:
        principal = client.principal()
    except caldav.lib.error.DAVError:
        return False
    except Exception:
        return False
    return principal.calendars()
