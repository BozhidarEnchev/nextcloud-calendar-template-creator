FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml uv.lock alembic.ini README.md ./
COPY alembic/ ./alembic/
COPY app/ ./app/

RUN pip install uv

RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
