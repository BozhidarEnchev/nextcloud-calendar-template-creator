from contextlib import asynccontextmanager
from decouple import config

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine
from app.dependencies import require_login
from app.models.user import User

from .routers import auth, nextcloud_account
from .templating import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=config("SECRET_KEY"))

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
app.include_router(router=auth.router)
app.include_router(router=nextcloud_account.router)


@app.get("/", response_class=HTMLResponse, name="index")
async def get_index(request: Request, current_user: User = Depends(require_login)):
    return templates.TemplateResponse(
        request=request, name="index.html",
        context={"current_user": current_user},
    )
