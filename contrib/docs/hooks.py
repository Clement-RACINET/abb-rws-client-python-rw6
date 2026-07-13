#!/usr/bin/env python3
# contrib/docs/hooks.py
"""
MkDocs hook: copy docs/htmlcov/ into site/htmlcov/ after each build.

Author: Clement RACINET

Registered in ``mkdocs.yml`` under the ``hooks:`` key. Called automatically
by MkDocs after every ``build`` or ``serve`` run.
"""
from __future__ import annotations

import shutil
from pathlib import Path


def on_post_build(config: dict[str, object]) -> None:
    """Copy the HTML coverage report into the generated site directory.

    Called automatically by MkDocs after each build or serve cycle.

    Args:
        config: MkDocs configuration dictionary (injected automatically).
    """
    src = Path(str(config["docs_dir"])) / "htmlcov"
    dst = Path(str(config["site_dir"])) / "htmlcov"

    if not src.exists():
        print(f"⚠️  hooks.py: {src} not found — run `pixi run test` first.")
        return

    if dst.exists():
        shutil.rmtree(dst)

    shutil.copytree(src, dst)
    print(f"✓ hooks.py: {src} → {dst}")
