from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.caldav_client import test_connection
from app.database import get_db
from app.dependencies import require_login
from app.models.nextcloud_account import NextcloudAccount
from app.models.user import User
from app.templating import templates
from app.security import decrypt_secret, encrypt_secret

router = APIRouter(prefix="/nextcloud-account")


@router.get("", name="nextcloud_account")
async def get_nextcloud_account(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    nc_acc = db.scalar(select(NextcloudAccount).where(NextcloudAccount.user_id == current_user.id))

    return templates.TemplateResponse(
        request=request,
        name="nextcloud_account/nextcloud_form.html",
        context={"nc_acc": nc_acc},
    )


@router.post("")
async def post_nextcloud_account(
    request: Request,
    username: str = Form(default=""),
    password: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    existing = db.scalar(select(NextcloudAccount).where(
        NextcloudAccount.user_id == current_user.id)
    )
    if existing is not None:
        if username:
            existing.username = username
        if password:
            existing.encrypted_password = encrypt_secret(password)
        db.commit()
        db.refresh(existing)
        return RedirectResponse(url=request.url_for("index"), status_code=status.HTTP_303_SEE_OTHER)
    nc_acc = NextcloudAccount(
        username=username,
        encrypted_password=encrypt_secret(password)
    )
    nc_acc.user_id = request.session["user_id"]
    db.add(nc_acc)
    db.commit()
    db.refresh(nc_acc)

    return RedirectResponse(url=request.url_for("nextcloud_account"), status_code=status.HTTP_303_SEE_OTHER)

@router.post("/delete", name="nextcloud_account_delete")
async def delete_nextcloud_account(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    nc_acc = db.scalar(select(NextcloudAccount).where(NextcloudAccount.user_id == current_user.id))
    if nc_acc is None:
        return RedirectResponse(url=request.url_for("index"), status_code=status.HTTP_303_SEE_OTHER)

    db.delete(nc_acc)
    db.commit()
    return RedirectResponse(url=request.url_for("index"), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/test", name="nextcloud_account_test")
async def test_nextcloud_connection(
    request: Request,
    current_user: User = Depends(require_login),
):
    nc_acc = current_user.nextcloud_account
    if nc_acc is None:
        return templates.TemplateResponse(
            request=request,
            name="nextcloud_account/nextcloud_form.html",
            context={"nc_acc": None, "error": "No Nextcloud account connected yet."},
        )

    test_result = test_connection(nc_acc.username, decrypt_secret(nc_acc.encrypted_password))

    return templates.TemplateResponse(
        request=request,
        name="nextcloud_account/nextcloud_form.html",
        context={"nc_acc": nc_acc, "test_result": test_result},
    )
