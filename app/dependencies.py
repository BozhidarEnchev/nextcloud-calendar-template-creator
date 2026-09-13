from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    user = None if user_id is None else db.get(User, user_id)
    # Exposed to templates via the context processor in app/templating.py.
    request.state.current_user = user
    return user


def require_login(request: Request, user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": str(request.url_for("login-page"))},
        )
    return user
