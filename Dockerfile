FROM python:3.11

WORKDIR /app

RUN pip install poetry
RUN poetry config installer.max-workers 10

ARG APP_VARIANT=contextful
ENV POETRY_FLAGS="--with examples --no-interaction --no-ansi"

COPY ./pyproject.toml ./poetry.lock ./
RUN if [ "${APP_VARIANT}" = "local" ] ; then \
    poetry install ${POETRY_FLAGS} --no-root --extras local ; \
    else \
    poetry install ${POETRY_FLAGS} --no-root ; \
    fi

COPY . .
RUN if [ "${APP_VARIANT}" = "local" ] ; then \
    poetry install ${POETRY_FLAGS} --extras local ; \
    else \
    poetry install ${POETRY_FLAGS} ; \
    fi

EXPOSE 8080

ENTRYPOINT poetry run ./run_examples.py $APP_VARIANT
