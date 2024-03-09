FROM python:3.11

WORKDIR /app

RUN apt-get update \
    && apt-get install -y python3-opencv \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*


COPY requirements.txt .

RUN pip install --pre -U --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
