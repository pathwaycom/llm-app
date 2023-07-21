import argparse
import importlib
from dotenv import load_dotenv
import os


load_dotenv()


if __name__ == "__main__":

    mode = os.environ.get("PIPELINE_MODE", "contextful")
    scenario_module = importlib.import_module(f"pathway_pipelines.{mode}.app")

    scenario_module.run()
