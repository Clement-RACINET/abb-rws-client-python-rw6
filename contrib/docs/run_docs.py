#!/usr/bin/env python3
# contrib/docs/run_docs.py
"""
Documentation pipeline orchestrator.

Author: Clement RACINET

Generates the API reference pages, produces the coverage HTML report,
and starts ``mkdocs serve``.

Usage:
    python contrib/docs/run_docs.py
    pixi run docs          # if configured in pixi.toml
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from contrib.docs.config import build_config
from contrib.docs.generate_api import generate_api_docs, update_mkdocs_nav


def _generate_coverage(project_root: Path) -> None:
    """Run pytest to produce the HTML coverage report in ``docs/htmlcov/``.

    Args:
        project_root: Absolute path to the project root.
    """
    print("\n📊 Generating coverage report...")
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "--cov=abb_rws_client",
            "--cov-branch",
            "--cov-report=html:docs/htmlcov",
            "--no-header", "-q",
        ],
        cwd=project_root,
        check=False,
    )
    if result.returncode != 0:
        print("⚠️  Some tests failed — coverage report may be incomplete.")


def main() -> None:
    """Main entry point of the documentation pipeline.

    Runs the three pipeline stages in order:

    1. Generate API Markdown pages and update ``mkdocs.yml``.
    2. Run pytest and produce the HTML coverage report.
    3. Start ``mkdocs serve`` (blocking until Ctrl+C).
    """
    cfg = build_config()

    print("\n📁 Generating API pages...")
    nav = generate_api_docs(cfg)
    update_mkdocs_nav(cfg, nav)

    _generate_coverage(cfg.project_root)

    print("\n🚀 Starting mkdocs serve...  (Ctrl+C to stop)")
    try:
        subprocess.run(
            [sys.executable, "-m", "mkdocs", "serve"],
            cwd=cfg.project_root,
            check=True,
        )
    except (KeyboardInterrupt, subprocess.CalledProcessError):
        print("\n👋 Server stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
