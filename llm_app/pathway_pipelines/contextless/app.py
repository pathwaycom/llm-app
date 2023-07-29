import pathway as pw
from llm_app.config import Config
from llm_app.model_wrappers import OpenAIChatGPTModel


class QueryInputSchema(pw.Schema):
    query: str
    user: str


def run(config: Config):
    query, response_writer = pw.io.http.rest_connector(
        host=config.rest_host,
        port=config.rest_port,
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
    )

    model = OpenAIChatGPTModel(api_key=config.api_key)

    responses = query.select(
        query_id=pw.this.id,
        result=model.apply(
            pw.this.query,
            locator=config.model_locator,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        ),
    )

    response_writer(responses)

    pw.run()
