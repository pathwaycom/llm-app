# Use an official Python runtime as a parent image
FROM python:3.11

ARG APP_VARIANT=contextful

# Set the working directory in the container to /app
WORKDIR /app

COPY ./requirements ./requirements

RUN if [ "${APP_VARIANT}" = "local" ] ; then \
    cp ./requirements/hf-local.txt ./requirements.txt ; \
else \
    cp ./requirements/default.txt ./requirements.txt ; \
fi

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY data data
COPY llm_app llm_app

# Change the working directory to /app/llm_app
WORKDIR /app/llm_app

EXPOSE 8080

# Run main.py when the container launches
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
