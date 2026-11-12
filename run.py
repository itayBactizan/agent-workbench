"""CLI entry point.

  python run.py data_analyst "Explore data/sample.csv"      # one task
  python run.py data_analyst                                # interactive: asks for the task
  python run.py data_analyst --eval                         # run all eval cases
  python run.py data_analyst --eval --case churn_drivers    # run one eval case
"""
import argparse

from core.evals import run_evals
from core.runner import Agent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("agent", help="folder name under agents/")
    p.add_argument("task", nargs="?", help="the task; omit to be prompted")
    p.add_argument("--eval", action="store_true", help="run evals/cases.yaml")
    p.add_argument("--case", help="with --eval: run only this case id")
    args = p.parse_args()

    if args.eval:
        run_evals(args.agent, only=args.case)
        return

    agent = Agent(args.agent)
    try:
        agent.run(args.task or input("Task: "))
    finally:
        agent.close()


if __name__ == "__main__":
    main()
