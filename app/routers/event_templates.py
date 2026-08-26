from datetime import time
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.caldav_client import get_user_calendars
from app.database import get_db
from app.dependencies import require_login
from app.models.event_template import EventTemplate
from app.models.event_template_item import EventTemplateItem
from app.models.user import User
from app.templating import templates

router = APIRouter(prefix="/event-templates")


@router.get("", name="event_templates")
async def get_event_templates(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    event_templates = db.scalars(select(EventTemplate).where(EventTemplate.user_id == current_user.id))

    return templates.TemplateResponse(
        request=request,
        name="event_templates/event_templates.html",
        context={"event_templates": event_templates},
        status_code=status.HTTP_200_OK,
    )


@router.get("/new", name="event_templates_new")
async def new_event_templates(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    return templates.TemplateResponse(
        request=request,
        name="event_templates/event_templates_form.html",
        context={},
        status_code=status.HTTP_200_OK,
    )


@router.post("/new", name="event_templates_create")
async def create_event_template(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    current_user: User = Depends(require_login),
):
    event_template = EventTemplate(name=name)
    event_template.user_id = current_user.id

    db.add(event_template)
    db.commit()
    db.refresh(event_template)

    return RedirectResponse(url=request.url_for("event_templates"), status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{template_id}", name="event_template_edit")
async def edit_event_template(
    request: Request,
    template_id: int,
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

    context = {}

    event_template = db.scalar(
        select(EventTemplate).where(
            EventTemplate.id == template_id,
            EventTemplate.user_id == current_user.id
        )
    )

    if event_template is None:
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

    context["event_template"] = event_template
    context["calendars"] = []

    calendars = get_user_calendars(
        caldav_user=current_user.nextcloud_account.username,
        app_pasword=current_user.nextcloud_account.encrypted_password
    )
    if calendars:
        context["calendars"] = calendars

    return templates.TemplateResponse(
        request=request,
        name="event_templates/event_templates_form.html",
        context=context,
        status_code=status.HTTP_200_OK,
    )


@router.post("/{template_id}", name="event_template_update")
async def update_event_template(
    request: Request,
    template_id: int,
    name: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    event_template = db.scalar(
        select(EventTemplate).where(
            EventTemplate.id == template_id,
            EventTemplate.user_id == current_user.id
        )
    )
    if not event_template:
        return RedirectResponse(url=request.url_for("event_templates"), status_code=status.HTTP_303_SEE_OTHER)

    if name:
        event_template.name = name
        db.commit()

    return RedirectResponse(url=request.url_for("event_template_edit", template_id=event_template.id), status_code=status.HTTP_303_SEE_OTHER)


@router.delete("/{template_id}", name="event_template_delete")
async def delete_event_template(
    request: Request,
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    event_template = db.scalar(
        select(EventTemplate).where(
            EventTemplate.id == template_id,
            EventTemplate.user_id == current_user.id
        )
    )

    if event_template is None:
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

    db.delete(event_template)
    db.commit()

    return RedirectResponse(url=request.url_for("event_templates"), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{template_id}/items", name="event_template_items_create")
async def new_event_template_item(
    request: Request,
    template_id: int,
    title: str = Form(...),
    description: str = Form(default=""),
    location: str = Form(default=""),
    start_time: time = Form(...),
    end_time: time = Form(...),
    calendar_url: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),     
):
    event_template_item = EventTemplateItem(
        title=title,
        description=description,
        location=location,
        start_time=start_time,
        end_time=end_time,
        calendar_url=calendar_url,
        template_id=template_id,
    )
    template = db.scalar(select(EventTemplate).where(EventTemplate.id == template_id))
    if not template:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    if template.user_id != current_user.id:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    db.add(event_template_item)
    db.commit()
    db.refresh(event_template_item)

    return templates.TemplateResponse(
        request=request,
        name="event_templates/_item_row.html",
        context={"item": event_template_item, "event_template": template},
    )


@router.delete("/{template_id}/items/{item_id}", name="event_template_item_delete")
async def delete_event_template_item(
    request: Request,
    template_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    template = db.scalar(
        select(EventTemplate).where(
            EventTemplate.id == template_id,
            EventTemplate.user_id == current_user.id
        )
    )
    if not template:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    event_template_item = db.scalar(
        select(EventTemplateItem).where(
            EventTemplateItem.id == item_id,
            EventTemplateItem.template_id == template_id,
        )
    )
    if not event_template_item:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    db.delete(event_template_item)
    db.commit()

    return Response(status_code=status.HTTP_200_OK)
