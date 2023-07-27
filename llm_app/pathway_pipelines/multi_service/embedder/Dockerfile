FROM python:3.11

WORKDIR /app

COPY ./requirements ./requirements

RUN pip install --upgrade pip && \
    pip install -r ./requirements/ms-sen-transformers.txt

COPY llm_app/pathway_pipelines/multi_service/embedder llm_app
COPY llm_app/model_wrappers llm_app/model_wrappers

WORKDIR /app/llm_app

EXPOSE 8880

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
