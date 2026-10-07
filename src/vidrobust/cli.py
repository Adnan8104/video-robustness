"""Shared experiment entry point, with historical commands grouped in legacy/."""
import argparse
import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY_COMMANDS = {
    "fetch": ("initial", "fetch"), "run": ("initial", "run"),
    "diagnose": ("diagnostics", "run_diagnostics"),
    "compare": ("comparison", "run_comparison"),
    "controlled": ("controlled", "run_controlled"),
    "followup": ("failure_followup", "run_followup"),
    "isolate": ("kitten_isolation", "run_isolation"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["experiment", "demo", "check", *LEGACY_COMMANDS])
    parser.add_argument("config", nargs="?", help="Experiment config, relative to the repository root")
    parser.add_argument("--dry-run", action="store_true", help="Validate config and counts without downloads or inference")
    args = parser.parse_args()
    if args.command != "experiment" and (args.config or args.dry_run):
        parser.error("config and --dry-run apply only to experiment")
    if args.command == "experiment":
        if not args.config:
            parser.error("experiment requires a config path")
        from .experiment import experiment_plan, run_experiment
        if args.dry_run:
            print(json.dumps(experiment_plan(ROOT, args.config), indent=2))
        else:
            run_experiment(ROOT, args.config)
    elif args.command == "demo":
        import importlib.util
        import subprocess
        import sys
        if importlib.util.find_spec("streamlit") is None:
            parser.error("Install the demo with: uv sync --locked --extra demo")
        raise SystemExit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(ROOT / "demo.py"),
            "--server.address=127.0.0.1", "--server.headless=true", "--server.maxUploadSize=100",
            "--browser.gatherUsageStats=false"], cwd=ROOT))
    elif args.command == "check":
        import unittest
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
        if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
            raise SystemExit(1)
    else:
        module, function = LEGACY_COMMANDS[args.command]
        study = importlib.import_module(f"vidrobust.legacy.{module}")
        getattr(study, function)(ROOT)


if __name__ == "__main__":
    main()
