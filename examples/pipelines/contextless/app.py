"""
REST Microservice implementing a simple, contextless Chatbot.

The program responds to each query by directly forwarding it to the OpenAI API.

Usage:
In the root of this repository run:
`poetry run ./run_examples.py contextless`
or, if all dependencies are managed manually rather than using poetry
`python examples/pipelines/contextless/app.py`

You can also run this example directly in the environment with llm_app installed.

To call the REST API:
curl --data '{"user": "user", "query": "How to connect to Kafka in Pathway?"}' http://localhost:8080/ | jq
"""

import os

import pathway as pw
from pathway.xpacks.llm.llms import OpenAIChat, prompt_chat_single_qa


class QueryInputSchema(pw.Schema):
    query: str
    user: str


def run(
    *,
    api_key: str = os.environ.get("OPENAI_API_KEY", ""),
    host: str = "0.0.0.0",
    port: int = 8080,
    model_locator: str = "gpt-3.5-turbo",
    max_tokens: int = 60,
    temperature: float = 0.8,
    **kwargs,
):
    query, response_writer = pw.io.http.rest_connector(
        host=host,
        port=port,
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
        delete_completed_queries=True,
    )

    model = OpenAIChat(
        model=model_locator,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        retry_strategy=pw.asynchronous.FixedDelayRetryStrategy(),
        cache_strategy=pw.asynchronous.DefaultCache(),
    )

    responses = query.select(
        query_id=pw.this.id,
        result=model(prompt_chat_single_qa(pw.this.query)),
    )

    response_writer(responses)

    pw.run()


if __name__ == "__main__":
    run()
