FROM python:3.11

WORKDIR /app

COPY ./requirements ./requirements

RUN pip install --upgrade pip && \
    pip install -r ./requirements/llama-cpp.txt

COPY llm_app/pathway_pipelines/multi_service/llm llm_app
COPY llm_app/model_wrappers llm_app/model_wrappers

WORKDIR /app/llm_app

EXPOSE 8888

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
