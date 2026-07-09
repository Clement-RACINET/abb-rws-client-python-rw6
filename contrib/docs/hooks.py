# contrib/docs/hooks.py
"""Hook MkDocs : copie docs/htmlcov/ dans site/htmlcov/ après le build."""
from __future__ import annotations

import shutil
from pathlib import Path


def on_post_build(config: dict[str, object]) -> None:
    """Copie le rapport coverage HTML dans le site généré.

    Appelé automatiquement par MkDocs après chaque build/serve.

    Args:
        config: Configuration MkDocs (injectée automatiquement).
    """
    src = Path(str(config["docs_dir"])) / "htmlcov"
    dst = Path(str(config["site_dir"])) / "htmlcov"

    if not src.exists():
        print(f"⚠️  hooks.py : {src} introuvable — lance d'abord `pixi run test`.")
        return

    if dst.exists():
        shutil.rmtree(dst)

    shutil.copytree(src, dst)
    print(f"✅ hooks.py : {src} → {dst}")
