FROM pathwaycom/pathway:latest
WORKDIR /app

RUN apt-get update \
    && apt-get install -y python3-opencv \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*
    
COPY . .
EXPOSE 8080

CMD ["python", "app.py"]
