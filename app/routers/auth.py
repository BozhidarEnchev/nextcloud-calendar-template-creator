from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security import hash_password, verify_password
from app.templating import templates

router = APIRouter(prefix="/users")


@router.get("/register", response_class=HTMLResponse)
async def get_register(request: Request):
    return templates.TemplateResponse(
        request=request, name="auth/register.html", context={},
    )


@router.post("/register")
async def post_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(User).where(User.username == username))
    if existing is not None:
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={"error": "That username is already taken."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = User(username=username, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse(
        request=request, name="auth/login.html", context={},
    )


@router.post("/login")
async def post_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(user.hashed_password, password):
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={"error": "Incorrect username or password."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
async def post_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/users/login",
                            status_code=status.HTTP_303_SEE_OTHER)
