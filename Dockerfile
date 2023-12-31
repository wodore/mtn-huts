FROM python:3.11-buster as builder

RUN pip install poetry==1.4.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root

FROM python:3.11-slim-buster as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"


RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# de_CH UTF-8/de_CH UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

ENV LANG de_CH.UTF-8
ENV LC_ALL de_CH.UTF-8

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY main ./main

ENTRYPOINT ["gunicorn", "main.main:app", "--bind", "0.0.0.0:80"]
