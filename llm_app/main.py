from llm_app.config import Config
from llm_app.pathway_pipelines.contextful.app import run as run_contextful
from llm_app.pathway_pipelines.contextful_s3.app import run as run_contextful_s3
from llm_app.pathway_pipelines.contextless.app import run as run_contextless
from llm_app.pathway_pipelines.local.app import run as run_local


apps = dict(
    contextful=run_contextful,
    contextful_s3=run_contextful_s3,
    contextless=run_contextless,
    local=run_local,
)


def run(config: Config):
    return apps[config.app_variant](config)
