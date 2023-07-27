import os
import pathway as pw
from model_wrappers import LlamaCPP


HTTP_HOST = os.environ.get("MODEL_REST_CONNECTOR_HOST", "127.0.0.1")
HTTP_PORT = os.environ.get("MODEL_REST_CONNECTOR_PORT", "8888")

# Download first the model.
# e.g. wget https://huggingface.co/localmodels/Llama-2-7B-ggml/resolve/main/llama-2-7b.ggmlv3.q2_K.bin

MODEL_LOCATOR = os.environ.get("MODEL_LOCATOR", "llama-2-7b.ggmlv3.q2_K.bin")

if not os.path.isfile(f"./{MODEL_LOCATOR}"):
    raise FileNotFoundError(f"File does {MODEL_LOCATOR} not exist.")


class InputSchema(pw.Schema):
    text: str


def run():
    prompt, response_writer = pw.io.http.rest_connector(
        host=HTTP_HOST,
        port=int(HTTP_PORT),
        schema=InputSchema,
        autocommit_duration_ms=50,
    )

    model = LlamaCPP(model=MODEL_LOCATOR)

    responses = prompt.select(
        result=model.apply(pw.this.text, echo=False, max_tokens=60),
    )

    response_writer(responses)

    pw.run()


if __name__ == "__main__":
    run()
