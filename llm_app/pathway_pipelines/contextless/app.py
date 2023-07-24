import os

import pathway as pw
from model_wrappers import OpenAIChatGPTModel


class QueryInputSchema(pw.Schema):
    query: str
    user: str


HTTP_HOST = os.environ.get("PATHWAY_REST_CONNECTOR_HOST", "127.0.0.1")
HTTP_PORT = os.environ.get("PATHWAY_REST_CONNECTOR_PORT", "8080")
API_KEY = os.environ.get("OPENAI_API_TOKEN")
MODEL_LOCATOR = "gpt-3.5-turbo" #  Change to 'gpt-4' if you have access.
TEMPERATURE = 0.0
MAX_TOKENS = 50


def run():
    query, response_writer = pw.io.http.rest_connector(
        host=HTTP_HOST,
        port=int(HTTP_PORT),
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
    )

    model = OpenAIChatGPTModel(api_key=API_KEY)

    responses = query.select(
        query_id=pw.this.id,
        result=model.apply(
            pw.this.query,
            locator=MODEL_LOCATOR,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        ),
    )

    response_writer(responses)

    pw.run()
