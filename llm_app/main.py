import argparse
from dotenv import load_dotenv
from llm_app.pathway_pipelines.contextful.app import run as run_contextful
from llm_app.pathway_pipelines.contextful_s3.app import run as run_contextful_s3
from llm_app.pathway_pipelines.contextless.app import run as run_contextless
from llm_app.pathway_pipelines.local.app import run as run_local


load_dotenv()
apps = dict(
    contextful=run_contextful,
    contextful_s3=run_contextful_s3,
    contextless=run_contextless,
    local=run_local,
)


def run():
    parser = argparse.ArgumentParser(description="Run the app with specified variant")
    parser.add_argument(
        "--app_variant",
        default="contextful",
        choices=list(apps.keys()),
        help="App variant to run",
    )

    args = parser.parse_args()

    return apps[args.app_variant]()
