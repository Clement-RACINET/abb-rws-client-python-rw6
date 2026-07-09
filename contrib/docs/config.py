# contrib/docs/config.py
"""Configuration centralisée pour la pipeline de documentation MkDocs.

Ce module est le seul point de vérité pour les chemins et paramètres
utilisés par generate_api.py et run_docs.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Racine du projet = 2 niveaux au-dessus de contrib/docs/
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]


@dataclass
class DocConfig:
    """Paramètres de la pipeline documentaire.

    Attributes:
        project_root: Racine absolue du projet.
        mkdocs_path: Chemin vers mkdocs.yml.
        docs_src_dir: Dossier source des fichiers Markdown.
        docs_api_dir: Sous-dossier généré automatiquement (API Reference).
        packages_to_scan: Liste des packages Python à documenter.
        exclude_dirs: Noms de dossiers à ignorer lors du scan.
        exclude_files: Noms de fichiers à ignorer lors du scan.
    """

    project_root: Path
    mkdocs_path: Path
    docs_src_dir: Path
    docs_api_dir: Path
    packages_to_scan: list[str]
    exclude_dirs: set[str] = field(default_factory=set)
    exclude_files: set[str] = field(default_factory=set)


def build_config() -> DocConfig:
    """Construit la configuration pour le projet abb_rws_client.

    Returns:
        DocConfig: Instance de configuration prête à l'emploi.

    Example:
        >>> from contrib.docs.config import build_config
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
            "contrib",
        },
        exclude_files={
            "__init__.py",
            "test_*.py",
        },
    )
