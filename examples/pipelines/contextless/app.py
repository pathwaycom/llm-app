"""
Usage:
In the root of this repository run:
`poetry run ./run_examples.py contextless`

You can also run this example directly in the environment with llm_app instaslled.

To call the REST API:
curl --data '{"user": "user", "query": "How to connect to Kafka in Pathway?"}' http://localhost:8080/ | jq
"""

import os

import pathway as pw

from llm_app.model_wrappers import OpenAIChatGPTModel


class QueryInputSchema(pw.Schema):
    query: str
    user: str


def run(
    *,
    api_key: str = os.environ.get("OPENAI_API_TOKEN", ""),
    host: str = "0.0.0.0",
    port: int = 8080,
    model_locator: str = "gpt2",
    max_tokens: int = 60,
    temperature: int = 0.8,
    **kwargs,
):
    query, response_writer = pw.io.http.rest_connector(
        host=host,
        port=port,
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
    )

    model = OpenAIChatGPTModel(api_key=api_key)

    responses = query.select(
        query_id=pw.this.id,
        result=model.apply(
            pw.this.query,
            locator=model_locator,
            temperature=temperature,
            max_tokens=max_tokens,
        ),
    )

    response_writer(responses)

    pw.run()


if __name__ == "__main__":
    run()
