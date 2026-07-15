#!/usr/bin/env python3
# utils/docs/config.py
"""
Documentation pipeline configuration for abb_rws_client.

Author: Clement RACINET

Single source of truth for all paths and parameters used by
``generate_api.py`` and ``run_docs.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

#: Absolute path to the project root (2 levels above utils/docs/)
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]


@dataclass
class DocConfig:
    """Documentation pipeline parameters.

    Attributes:
        project_root: Absolute path to the project root.
        mkdocs_path: Path to ``mkdocs.yml``.
        docs_src_dir: Source directory for Markdown files.
        docs_api_dir: Auto-generated sub-directory (API Reference).
        packages_to_scan: List of Python packages to document.
        exclude_dirs: Directory names to skip during the scan.
        exclude_files: File name patterns to skip during the scan (fnmatch).
        balise_api_debut: Opening tag of the AUTOGEN section in ``mkdocs.yml``.
        balise_api_fin: Closing tag of the AUTOGEN section in ``mkdocs.yml``.
    """

    project_root: Path
    mkdocs_path: Path
    docs_src_dir: Path
    docs_api_dir: Path
    packages_to_scan: list[str]
    exclude_dirs: set[str] = field(default_factory=set)
    exclude_files: set[str] = field(default_factory=set)
    balise_api_debut: str = "# --- AUTOGEN_API_START ---"
    balise_api_fin: str = "# --- AUTOGEN_API_END ---"


def build_config() -> DocConfig:
    """Build the documentation pipeline configuration for abb_rws_client.

    Returns:
        A fully populated ``DocConfig`` instance ready for use.

    Example:
        >>> from utils.docs.config import build_config
        >>> cfg = build_config()
        >>> cfg.project_root.name
        'abb_rws_client_python_rw6'
    """
    return DocConfig(
        project_root=PROJECT_ROOT,
        mkdocs_path=PROJECT_ROOT / "mkdocs.yml",
        docs_src_dir=PROJECT_ROOT / "docs",
        docs_api_dir=PROJECT_ROOT / "docs" / "api",
        packages_to_scan=["abb_rws_client"],
        exclude_dirs={
            "__pycache__",
            ".pytest_cache",
            ".git",
            ".pixi",
            "abb_rws_client.egg-info",
            "utils",
        },
        exclude_files={
            "__init__.py",
            "test_*.py",
        },
        balise_api_debut="# --- AUTOGEN_API_START ---",
        balise_api_fin="# --- AUTOGEN_API_END ---",
    )
