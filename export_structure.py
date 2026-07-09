from pathlib import Path

# Dossier racine du repo actuel
ROOT_DIR = Path(".").resolve()

# Fichier de sortie
OUTPUT_FILE = ROOT_DIR / "structure_repo.txt"

# Dossiers à ignorer
IGNORE_DIRS = {
    ".git",
    ".pixi"
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".idea",
    ".vscode",
    "dist",
    "build",
}

# Fichiers à ignorer si besoin
IGNORE_FILES = {
    ".DS_Store",
}


def should_ignore(path: Path) -> bool:
    """
    Retourne True si le chemin doit être ignoré.
    """
    if path.name in IGNORE_DIRS or path.name in IGNORE_FILES:
        return True

    # Ignore aussi les éléments contenus dans un dossier ignoré
    return any(parent.name in IGNORE_DIRS for parent in path.parents)


def generate_tree(directory: Path, prefix: str = "") -> list[str]:
    """
    Génère une représentation en arbre du dossier donné.
    """
    entries = sorted(
        [p for p in directory.iterdir() if not should_ignore(p)],
        key=lambda p: (p.is_file(), p.name.lower())
    )

    lines = []

    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = "    " if index == len(entries) - 1 else "│   "
            lines.extend(generate_tree(entry, prefix + extension))

    return lines


def main():
    tree_lines = [ROOT_DIR.name]
    tree_lines.extend(generate_tree(ROOT_DIR))

    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    OUTPUT_FILE.write_text("\n".join(tree_lines), encoding="utf-8") 

    print(f"Structure du repo exportée dans : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
