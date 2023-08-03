# Use an official Python runtime as a parent image
FROM python:3.11

ARG APP_VARIANT=contextful

# Set the working directory in the container to /app
WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip 


RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

# Change the working directory to /app/llm_app
WORKDIR /app/llm_app

EXPOSE 8080

# Run main.py when the container launches
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
