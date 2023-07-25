import os
import pathway as pw
from model_wrappers import HFTextGenerationTask


HTTP_HOST = os.environ.get("MODEL_REST_CONNECTOR_HOST", "127.0.0.1")
HTTP_PORT = os.environ.get("MODEL_REST_CONNECTOR_PORT", "8888")
MODEL_LOCATOR = "gpt2"


class PromptInputSchema(pw.Schema):
    prompt: str


def run():
    prompt, response_writer = pw.io.http.rest_connector(
        host=HTTP_HOST,
        port=int(HTTP_PORT),
        schema=PromptInputSchema,
        autocommit_duration_ms=50,
    )

    model = HFTextGenerationTask(model=MODEL_LOCATOR)

    responses = prompt.select(
        result=model.apply(pw.this.prompt, return_full_text=False, max_new_tokens=60),
    )

    response_writer(responses)

    pw.run()
