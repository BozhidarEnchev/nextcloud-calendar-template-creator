from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from .templating import templates

app = FastAPI()
app.mount('/static', StaticFiles(directory='app/web/static'), name='static')


@app.get('/', response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(
        request=request, name='index.html', context={},
    )
