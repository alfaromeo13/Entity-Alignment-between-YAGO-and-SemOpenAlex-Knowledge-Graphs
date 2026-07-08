#!/usr/bin/env python3
"""Run the complete maintained thesis-visualization workflow."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def run(name, refresh=False):
    command = [sys.executable, str(SCRIPT_DIR / name)]
    if refresh:
        command.append("--refresh")
    print(f"\n=== {name} ===", flush=True)
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Rescan full source files instead of reusing statistical caches.",
    )
    args = parser.parse_args()
    run("make_thesis_figures.py", args.refresh)
    run("make_link_prediction_extensions.py", args.refresh)
    # Produce Tables 26–27 before the combined table index is rebuilt by the
    # additional-figure generator.
    run("make_structural_validation_figures.py", args.refresh)
    run("make_ontology_schema_figures.py", False)
    run("make_supported_extension_figures.py", args.refresh)
    run("make_distribution_extensions.py", args.refresh)
    run("make_additional_figures.py", args.refresh)
    run("make_reporting_additions.py", args.refresh)
    run("make_visual_story_figures.py", False)


if __name__ == "__main__":
    main()
