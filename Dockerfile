FROM python:3.9.5 AS base

FROM base as build

# renovate: datasource=github-releases depName=python-poetry/poetry
ARG POETRY_VERSION=1.1.6
ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/${POETRY_VERSION}/get-poetry.py | python -
ENV PATH=$PATH:${POETRY_HOME}/bin

COPY pyproject.toml poetry.lock /app/
WORKDIR /app
RUN POETRY_VIRTUALENVS_IN_PROJECT=true poetry install && \
    . .venv/bin/activate && VENV_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])") && \
    mv $VENV_PACKAGES /app/lib

FROM base

WORKDIR /app

COPY . .
COPY --from=build /app/lib /app/lib
ENV PYTHONPATH=/app/lib

ENTRYPOINT [ "python", "-m", "radio_db" ]
