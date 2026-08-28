from datetime import date

from fastapi import APIRouter, Depends, Form, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.caldav_client import create_event
from app.database import get_db
from app.dependencies import require_login
from app.models.event_template import EventTemplate
from app.models.user import User
from app.templating import templates

router = APIRouter(prefix="/events")


@router.post("", name="events_create")
async def create_events(
    request: Request,
    template_id: int = Form(...),
    event_date: date = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    if current_user.nextcloud_account is None:
        return templates.TemplateResponse(
            request=request,
            name="errors/message.html",
            context={
                "heading": "No Nextcloud account added!",
                "message": "Add account before you continue!",
                "link_url": request.url_for("nextcloud_account"),
                "link_text": "Connect Nextcloud account",
            },
            status_code=status.HTTP_403_FORBIDDEN,
        )

    template = db.scalar(
        select(EventTemplate).where(
            EventTemplate.id == template_id,
            EventTemplate.user_id == current_user.id,
        )
    )
    if template is None:
        return templates.TemplateResponse(
            request=request,
            name="errors/message.html",
            context={
                "heading": "Template not found",
                "message": "This template doesn't exist or isn't yours.",
                "link_url": request.url_for("event_templates"),
                "link_text": "Back to templates",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if not template.items:
        return templates.TemplateResponse(
            request=request,
            name="errors/message.html",
            context={
                "heading": "Template has no items",
                "message": "This template has no items to create events from.",
                "link_url": request.url_for("event_templates"),
                "link_text": "Back to templates",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    results = []
    for item in template.items:
        success = create_event(
            caldav_user=current_user.nextcloud_account.username,
            app_pasword=current_user.nextcloud_account.encrypted_password,
            item=item,
            event_date=event_date,
        )
        results.append({"item": item, "success": success})

    return templates.TemplateResponse(
        request=request,
        name="events_result.html",
        context={"template": template, "event_date": event_date, "results": results},
    )
