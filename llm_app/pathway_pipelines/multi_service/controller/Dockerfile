FROM python:3.11

WORKDIR /app

COPY ./requirements ./requirements

RUN pip install --upgrade pip && \
    pip install -r ./requirements/default.txt

COPY data data
COPY llm_app/pathway_pipelines/multi_service/controller llm_app
COPY llm_app/model_wrappers llm_app/model_wrappers

WORKDIR /app/llm_app

EXPOSE 8080

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
