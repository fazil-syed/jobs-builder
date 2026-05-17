FROM mcr.microsoft.com/playwright/python:v1.59.0-noble

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --no-interaction


COPY . .

CMD [ "poetry", "run", "python", "-m", "app.main" ]