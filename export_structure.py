from pathlib import Path
import pathspec

# Dossier racine du repo actuel
ROOT_DIR = Path(".").resolve()

# Fichier de sortie
OUTPUT_FILE = ROOT_DIR / "structure_repo.txt"

# Ignorés "en dur" supplémentaires (optionnel)
EXTRA_IGNORE = {
    ".git",  # souvent déjà dans .gitignore, mais on force ici
    OUTPUT_FILE.name,  # évite que le fichier généré se ré-inclue
}

def load_gitignore_spec(root: Path) -> pathspec.PathSpec:
    """
    Charge les patterns de .gitignore et retourne un PathSpec.
    """
    gitignore_path = root / ".gitignore"
    patterns = []

    if gitignore_path.exists():
        patterns = gitignore_path.read_text(encoding="utf-8").splitlines()

    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)

def should_ignore(path: Path, spec: pathspec.PathSpec, root: Path) -> bool:
    """
    Retourne True si le chemin doit être ignoré selon .gitignore
    ou selon les exclusions supplémentaires.
    """
    rel = path.relative_to(root)
    rel_str = rel.as_posix()

    if path.name in EXTRA_IGNORE:
        return True

    # Pour les dossiers, on ajoute "/" pour bien matcher les règles de dossier
    if path.is_dir():
        rel_str += "/"

    return spec.match_file(rel_str)

def generate_tree(directory: Path, spec: pathspec.PathSpec, root: Path, prefix: str = "") -> list[str]:
    """
    Génère une représentation en arbre du dossier donné.
    """
    entries = sorted(
        [p for p in directory.iterdir() if not should_ignore(p, spec, root)],
        key=lambda p: (p.is_file(), p.name.lower())
    )

    lines = []

    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = "    " if index == len(entries) - 1 else "│   "
            lines.extend(generate_tree(entry, spec, root, prefix + extension))

    return lines

def main():
    spec = load_gitignore_spec(ROOT_DIR)

    tree_lines = [ROOT_DIR.name]
    tree_lines.extend(generate_tree(ROOT_DIR, spec, ROOT_DIR))

    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    OUTPUT_FILE.write_text("\n".join(tree_lines), encoding="utf-8")
    print(f"Structure du repo exportée dans : {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
