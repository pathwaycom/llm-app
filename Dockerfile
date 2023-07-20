# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && \
    pip install --extra-index-url https://packages.pathway.com/966431ef6ba -r requirements.txt

# Change the working directory to /app/llm_app
WORKDIR /app/llm_app

# Make port 80 available to the world outside this container
EXPOSE 8080

# Run main.py when the container launches
CMD ["python", "main.py", "--mode", "contextful"]
