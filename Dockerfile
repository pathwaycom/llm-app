FROM python:3.11

WORKDIR /app

RUN pip install poetry
RUN poetry config installer.max-workers 10

ARG APP_VARIANT=contextful

COPY ./pyproject.toml ./pyproject.toml
COPY ./poetry.lock ./poetry.lock

RUN if [ "${APP_VARIANT}" = "local" ] ; then \
    poetry install --no-root --with examples --no-interaction --no-ansi --extras local; \
    else \
    poetry install --no-root --with examples --no-interaction --no-ansi  ; \
    fi

COPY . .
RUN poetry install --only-root

EXPOSE 8080

ENTRYPOINT poetry run ./run_examples.py $APP_VARIANT
