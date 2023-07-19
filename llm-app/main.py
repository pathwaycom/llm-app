import argparse
import importlib

from dotenv import load_dotenv

load_dotenv()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM App Pathway")

    parser.add_argument(
        "--mode",
        type=str,
        choices=["contextful", "contextless", "local"],
        default="contextful",
        help="Which pathway logic to run (default: %(default)s)",
    )

    args = parser.parse_args()
    scenario_module = importlib.import_module(f"pathway_pipelines.{args.mode}.app")

    scenario_module.run()
