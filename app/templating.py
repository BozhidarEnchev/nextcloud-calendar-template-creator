from fastapi import Request
from fastapi.templating import Jinja2Templates


def current_user_context(request: Request) -> dict:
    # get_current_user() stashes the loaded User on request.state, so every
    # template (the navbar in base.html especially) can see who is logged in
    # without each route having to pass current_user into its context.
    return {"current_user": getattr(request.state, "current_user", None)}


templates = Jinja2Templates(
    directory="app/web/templates",
    context_processors=[current_user_context],
)
