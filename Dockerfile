# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container to /app
WORKDIR /app

COPY requirements.txt requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && \
    pip install --extra-index-url https://packages.pathway.com/966431ef6ba -r requirements.txt

COPY data data
COPY llm_app llm_app

# Change the working directory to /app/llm_app
WORKDIR /app/llm_app

EXPOSE 8080

# Run main.py when the container launches
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
