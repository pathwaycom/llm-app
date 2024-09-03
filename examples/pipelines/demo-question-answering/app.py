import logging

import pathway as pw
from dotenv import load_dotenv
from pathway.xpacks import llm
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pydantic import BaseModel, ConfigDict, InstanceOf
from typing_extensions import TypedDict

# To use advanced features with Pathway Scale, get your free license key from
# https://pathway.com/features and paste it below.
# To use Pathway Community, comment out the line below.
pw.set_license_key("demo-license-key-with-telemetry")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

load_dotenv()

host_config = TypedDict("host_config", {"host": str, "port": int})


class App(BaseModel):
    llm: InstanceOf[pw.UDF]
    embedder: InstanceOf[llm.embedders.BaseEmbedder]
    splitter: InstanceOf[pw.UDF]
    parser: InstanceOf[pw.UDF]

    sources: list[InstanceOf[pw.Table]]

    host_config: host_config

    def run(self, config_file: str = "config.yaml") -> None:
        # Unpack host and port from config
        host, port = self.host_config["host"], self.host_config["port"]

        doc_store = VectorStoreServer(
            *self.sources,
            embedder=self.embedder,
            splitter=self.splitter,
            parser=self.parser,
        )

        rag_app = BaseRAGQuestionAnswerer(llm=self.llm, indexer=doc_store)

        rag_app.build_server(host=host, port=port)

        rag_app.run_server(with_cache=True, terminate_on_error=False)

    model_config = ConfigDict(extra="forbid")


if __name__ == "__main__":
    with open("config.yaml") as f:
        config = pw.load_yaml(f)
    app = App(**config)
    app.run()
