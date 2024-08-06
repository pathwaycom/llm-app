FROM pathwaycom/pathway:0.14.1-slim

ENV DOCKER_BUILDKIT=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    poppler-utils \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-app.txt requirements-app.txt

RUN pip install -U --no-cache-dir -r requirements-app.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
