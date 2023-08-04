# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container to /app
WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip 


RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

EXPOSE 8080

ENTRYPOINT "./run_examples.py" $APP_VARIANT
