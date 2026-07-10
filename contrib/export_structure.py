#!/usr/bin/env python3
# export_structure.py
"""
Repository tree exporter.

Author: Clément RACINET

Walks the repository from its root, respects ``.gitignore`` patterns via
``pathspec``, and writes a Unicode tree representation to
``structure_repo.txt``.

Usage:
    python export_structure.py

Output:
    <project_root>/structure_repo.txt
"""
from __future__ import annotations

from pathlib import Path

import pathspec

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

#: Absolute path to the repository root (resolved from the working directory)
ROOT_DIR: Path = Path(".").resolve()

#: Output file written at the project root
OUTPUT_FILE: Path = ROOT_DIR / "structure_repo.txt"

#: Hard-coded exclusions applied regardless of ``.gitignore`` content
EXTRA_IGNORE: set[str] = {
    ".git",           # usually already in .gitignore, forced here as a safety net
    OUTPUT_FILE.name, # prevent the output file from including itself
    "site",
    "docs"
}


# ---------------------------------------------------------------------------
# .gitignore loading
# ---------------------------------------------------------------------------


def load_gitignore_spec(root: Path) -> pathspec.PathSpec:
    """Load ``.gitignore`` patterns and return a compiled ``PathSpec``.

    If no ``.gitignore`` file is found, returns an empty spec (nothing
    is ignored by default).

    Args:
        root: Absolute path to the repository root.

    Returns:
        A ``pathspec.PathSpec`` compiled from ``gitwildmatch`` patterns.

    Example:
        >>> spec = load_gitignore_spec(Path("/my/project"))
        >>> spec.match_file("__pycache__/")
        True
    """
    gitignore_path = root / ".gitignore"
    patterns: list[str] = []

    if gitignore_path.exists():
        patterns = gitignore_path.read_text(encoding="utf-8").splitlines()

    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


# ---------------------------------------------------------------------------
# Exclusion predicate
# ---------------------------------------------------------------------------


def should_ignore(path: Path, spec: pathspec.PathSpec, root: Path) -> bool:
    """Return whether a path should be excluded from the tree.

    Applies both ``EXTRA_IGNORE`` hard-coded names and the compiled
    ``.gitignore`` spec. Directories are matched with a trailing ``/``
    to correctly trigger directory-specific gitignore rules.

    Args:
        path: Absolute path to the file or directory to test.
        spec: Compiled ``PathSpec`` from ``.gitignore``.
        root: Absolute path to the repository root.

    Returns:
        ``True`` if the path must be excluded.

    Example:
        >>> should_ignore(Path("/project/.git"), spec, Path("/project"))
        True
    """
    if path.name in EXTRA_IGNORE:
        return True

    rel_str = path.relative_to(root).as_posix()
    if path.is_dir():
        rel_str += "/"

    return spec.match_file(rel_str)


# ---------------------------------------------------------------------------
# Tree generator
# ---------------------------------------------------------------------------


def generate_tree(
    directory: Path,
    spec: pathspec.PathSpec,
    root: Path,
    prefix: str = "",
) -> list[str]:
    """Recursively generate a Unicode tree representation of a directory.

    Directories are listed before files at each level. Entries ignored
    by ``should_ignore()`` are skipped entirely.

    Args:
        directory: Directory to render.
        spec: Compiled ``PathSpec`` from ``.gitignore``.
        root: Absolute path to the repository root (used for relative
            path computation).
        prefix: Current line prefix (box-drawing characters accumulated
            through recursion). Defaults to ``""``.

    Returns:
        List of formatted tree lines for ``directory`` and all its
        non-excluded descendants.

    Example:
        >>> lines = generate_tree(Path("/project"), spec, Path("/project"))
        >>> lines[0]
        '├── abb_rws_client'
    """
    entries = sorted(
        [p for p in directory.iterdir() if not should_ignore(p, spec, root)],
        key=lambda p: (p.is_file(), p.name.lower()),
    )

    lines: list[str] = []

    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = "    " if index == len(entries) - 1 else "│   "
            lines.extend(generate_tree(entry, spec, root, prefix + extension))

    return lines


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate the repository tree and write it to ``structure_repo.txt``.

    Loads ``.gitignore``, walks the full repository tree, and writes the
    result to ``OUTPUT_FILE``. Any pre-existing output file is removed
    before writing.
    """
    spec = load_gitignore_spec(ROOT_DIR)

    tree_lines = [ROOT_DIR.name]
    tree_lines.extend(generate_tree(ROOT_DIR, spec, ROOT_DIR))

    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    OUTPUT_FILE.write_text("\n".join(tree_lines), encoding="utf-8")
    print(f"Repository structure exported to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
