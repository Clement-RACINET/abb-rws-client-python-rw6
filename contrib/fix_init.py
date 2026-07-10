#!/usr/bin/env python3
# contrib/fix_init.py
"""
Audit and auto-fix all __init__.py files in abb_rws_client/ and tests/.

For each Python package directory (containing .py files or sub-packages):
  - Creates __init__.py if missing.
  - Rewrites abb_rws_client/rws/*/__init__.py with correct imports + __all__.
  - Rewrites abb_rws_client/__init__.py with public API exports.
  - Rewrites abb_rws_client/_core/__init__.py with core exports.
  - Rewrites tests/__init__.py and tests/rws/**/__init__.py as empty markers.

Usage:
    pixi run python contrib/fix_init.py
    pixi run python contrib/fix_init.py --dry-run

Args:
    --dry-run: Print what would be written without touching the filesystem.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
PKG_ROOT = REPO_ROOT / "abb_rws_client"
TESTS_ROOT = REPO_ROOT / "tests"

# Modules _core exportés publiquement depuis abb_rws_client/
_CORE_PUBLIC_EXPORTS: dict[str, list[str]] = {
    "client": ["RWSClient", "RWSClientSync"],
    "exceptions": [
        "RWSError",
        "RWSConnectionError",
        "RWSTimeoutError",
        "RWSAuthenticationError",
        "RWSHTTPError",
        "RWSNotFoundError",
        "MastershipError",
        "MastershipDenied",
        "MastershipNotHeld",
        "RWSValueError",
        "CTRL_CODES",
    ],
    "serializers": ["RobTarget", "RapidValue", "robtarget_to_rws", "rws_to_robtarget"],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _collect_public_names(py_file: Path) -> list[str]:
    """Parse a .py file with AST and return all top-level public names.

    Args:
        py_file: Path to the Python source file.

    Returns:
        Sorted list of public names (no leading underscore).
    """
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        print(f"  [WARN] Cannot parse {py_file}: {exc}", file=sys.stderr)
        return []

    names: list[str] = []
    for node in ast.walk(tree):
        match node:
            case ast.FunctionDef(name=n) | ast.AsyncFunctionDef(name=n):
                if not n.startswith("_"):
                    names.append(n)
            case ast.ClassDef(name=n):
                if not n.startswith("_"):
                    names.append(n)
            case ast.Assign(targets=targets, value=_):
                for t in targets:
                    if isinstance(t, ast.Name) and not t.id.startswith("_"):
                        names.append(t.id)
            case ast.AnnAssign(target=ast.Name(id=n)):
                if not n.startswith("_"):
                    names.append(n)

    # Deduplicate preserving first occurrence order
    seen: set[str] = set()
    result: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            result.append(n)
    return sorted(result)


def _write(path: Path, content: str, dry_run: bool) -> None:
    """Write content to path, or print it in dry-run mode.

    Args:
        path: Destination file path.
        content: File content to write.
        dry_run: If True, only print; do not write.
    """
    rel = path.relative_to(REPO_ROOT)
    if dry_run:
        print(f"\n{'='*60}")
        print(f"[DRY-RUN] Would write: {rel}")
        print(f"{'='*60}")
        print(content)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"  [OK] Written: {rel}")


def _is_package_dir(directory: Path) -> bool:
    """Return True if directory contains .py files or sub-packages.

    Args:
        directory: Directory to inspect.

    Returns:
        True if the directory qualifies as a Python package.
    """
    if not directory.is_dir():
        return False
    has_py = any(
        f.suffix == ".py" and f.name != "__init__.py"
        for f in directory.iterdir()
        if f.is_file()
    )
    has_subpkg = any(
        (d / "__init__.py").exists() or _is_package_dir(d)
        for d in directory.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )
    return has_py or has_subpkg


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def _gen_rws_submodule_init(pkg_dir: Path) -> str:
    """Generate __init__.py for a rws/ sub-package (e.g. rws/ctrl/).

    Imports all public names from every .py sibling (except __init__.py)
    and builds __all__.

    Args:
        pkg_dir: Path to the sub-package directory.

    Returns:
        Complete __init__.py content as a string.
    """
    py_files = sorted(
        f for f in pkg_dir.iterdir()
        if f.is_file() and f.suffix == ".py" and f.name != "__init__.py"
    )

    import_lines: list[str] = []
    all_names: list[str] = []

    for py_file in py_files:
        module_name = py_file.stem
        names = _collect_public_names(py_file)
        if names:
            names_str = ", ".join(names)
            import_lines.append(f"from .{module_name} import {names_str}")
            all_names.extend(names)

    all_list = "\n    ".join(f'"{n}",' for n in sorted(all_names))
    imports_block = "\n".join(import_lines) if import_lines else "# No public symbols"

    rel = pkg_dir.relative_to(PKG_ROOT)
    return f'''\
# abb_rws_client/{rel}/__init__.py
"""Public re-exports for the {rel} sub-package.

Auto-generated by contrib/fix_init.py — do not edit manually.
"""

from __future__ import annotations

{imports_block}

__all__ = [
    {all_list}
]
'''


def _gen_rws_init(rws_dir: Path) -> str:
    """Generate __init__.py for abb_rws_client/rws/.

    Re-exports everything from all sub-packages.

    Args:
        rws_dir: Path to abb_rws_client/rws/.

    Returns:
        Complete __init__.py content as a string.
    """
    sub_pkgs = sorted(
        d.name for d in rws_dir.iterdir()
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
    )

    import_lines = [f"from .{pkg} import *  # noqa: F401, F403" for pkg in sub_pkgs]
    imports_block = "\n".join(import_lines) if import_lines else "# No sub-packages"

    return f'''\
# abb_rws_client/rws/__init__.py
"""RWS API mirror — atomic HTTP functions (1 function = 1 endpoint).

Auto-generated by contrib/fix_init.py — do not edit manually.
Sub-packages: {", ".join(sub_pkgs)}
"""

from __future__ import annotations

{imports_block}
'''


def _gen_core_init() -> str:
    """Generate __init__.py for abb_rws_client/_core/.

    Returns:
        Complete __init__.py content as a string.
    """
    import_lines: list[str] = []
    all_names: list[str] = []

    for module, names in _CORE_PUBLIC_EXPORTS.items():
        names_str = ", ".join(names)
        import_lines.append(f"from .{module} import {names_str}")
        all_names.extend(names)

    imports_block = "\n".join(import_lines)
    all_list = "\n    ".join(f'"{n}",' for n in all_names)

    return f'''\
# abb_rws_client/_core/__init__.py
"""Internal core — session, exceptions, serializers.

Not part of the public API. Import from ``abb_rws_client`` directly.
"""

from __future__ import annotations

{imports_block}

__all__ = [
    {all_list}
]
'''


def _gen_package_init() -> str:
    """Generate abb_rws_client/__init__.py with the public API surface.

    Returns:
        Complete __init__.py content as a string.
    """
    client_names = ", ".join(_CORE_PUBLIC_EXPORTS["client"])
    exc_names = ", ".join(_CORE_PUBLIC_EXPORTS["exceptions"])
    ser_names = ", ".join(_CORE_PUBLIC_EXPORTS["serializers"])

    all_names = (
        _CORE_PUBLIC_EXPORTS["client"]
        + _CORE_PUBLIC_EXPORTS["exceptions"]
        + _CORE_PUBLIC_EXPORTS["serializers"]
    )
    all_list = "\n    ".join(f'"{n}",' for n in all_names)

    return f'''\
# abb_rws_client/__init__.py
"""abb-rws6-python-client — Async Python client for ABB RWS (RobotWare 6).

Public API surface:
    - RWSClient / RWSClientSync  : HTTP session management
    - RWSError hierarchy         : typed exceptions
    - RobTarget / RapidValue     : RAPID type helpers
    - robtarget_to_rws / rws_to_robtarget : serializers

Example:
    >>> from abb_rws_client import RWSClient
    >>> async with RWSClient(host="192.168.125.1") as client:
    ...     resp = await client.get("rw/rapid/execution")
"""

from __future__ import annotations

from abb_rws_client._core.client import {client_names}
from abb_rws_client._core.exceptions import {exc_names}
from abb_rws_client._core.serializers import {ser_names}

__all__ = [
    {all_list}
]

__version__ = "0.1.0"
'''


def _gen_empty_init(path: Path, comment: str = "") -> str:
    """Generate a minimal marker __init__.py.

    Args:
        path: Destination path (used for the header comment).
        comment: Optional one-line description.

    Returns:
        Minimal __init__.py content.
    """
    rel = path.relative_to(REPO_ROOT)
    body = f"# {comment}" if comment else "# Package marker — auto-generated."
    return f"# {rel}\n{body}\n"


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------


def fix_rws(dry_run: bool) -> None:
    """Process all rws/ sub-packages.

    Args:
        dry_run: If True, only print without writing.
    """
    rws_dir = PKG_ROOT / "rws"
    if not rws_dir.exists():
        print("[SKIP] abb_rws_client/rws/ not found — skipping.")
        return

    print("\n── rws/ sub-packages ──────────────────────────────────────")
    for sub in sorted(rws_dir.iterdir()):
        if not sub.is_dir() or sub.name.startswith("_") or sub.name.startswith("."):
            continue
        init_path = sub / "__init__.py"
        content = _gen_rws_submodule_init(sub)
        _write(init_path, content, dry_run)

    print("\n── rws/__init__.py ─────────────────────────────────────────")
    _write(rws_dir / "__init__.py", _gen_rws_init(rws_dir), dry_run)


def fix_core(dry_run: bool) -> None:
    """Rewrite _core/__init__.py.

    Args:
        dry_run: If True, only print without writing.
    """
    print("\n── _core/__init__.py ───────────────────────────────────────")
    _write(PKG_ROOT / "_core" / "__init__.py", _gen_core_init(), dry_run)


def fix_package(dry_run: bool) -> None:
    """Rewrite abb_rws_client/__init__.py.

    Args:
        dry_run: If True, only print without writing.
    """
    print("\n── abb_rws_client/__init__.py ──────────────────────────────")
    _write(PKG_ROOT / "__init__.py", _gen_package_init(), dry_run)


def fix_highlevel(dry_run: bool) -> None:
    """Ensure highlevel/ has an __init__.py.

    Args:
        dry_run: If True, only print without writing.
    """
    hl_dir = PKG_ROOT / "highlevel"
    if not hl_dir.exists():
        print("\n[SKIP] highlevel/ does not exist yet — skipping.")
        return

    print("\n── highlevel/__init__.py ───────────────────────────────────")
    init_path = hl_dir / "__init__.py"
    if not init_path.exists():
        _write(
            init_path,
            _gen_empty_init(init_path, "High-level composed wrappers (no direct HTTP)."),
            dry_run,
        )
    else:
        print(f"  [SKIP] Already exists: {init_path.relative_to(REPO_ROOT)}")


def fix_tests(dry_run: bool) -> None:
    """Ensure all test directories have an __init__.py.

    Args:
        dry_run: If True, only print without writing.
    """
    print("\n── tests/ ──────────────────────────────────────────────────")
    for dirpath in sorted(TESTS_ROOT.rglob("*")):
        if not dirpath.is_dir():
            continue
        if dirpath.name.startswith(".") or dirpath.name == "__pycache__":
            continue
        # Only create if there are .py files or sub-dirs inside
        if not _is_package_dir(dirpath):
            continue
        init_path = dirpath / "__init__.py"
        if not init_path.exists():
            _write(
                init_path,
                _gen_empty_init(init_path, "Test package marker."),
                dry_run,
            )
        else:
            print(f"  [SKIP] Already exists: {init_path.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point.

    Raises:
        SystemExit: On argument parsing error.
    """
    parser = argparse.ArgumentParser(
        description="Audit and fix all __init__.py files in the project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without touching the filesystem.",
    )
    args = parser.parse_args()

    dry = args.dry_run
    if dry:
        print("🔍 DRY-RUN mode — no files will be written.\n")
    else:
        print("🔧 Fixing __init__.py files...\n")

    fix_package(dry)
    fix_core(dry)
    fix_rws(dry)
    fix_highlevel(dry)
    fix_tests(dry)

    print("\n✓ Done." if not dry else "\n✓ Dry-run complete.")


if __name__ == "__main__":
    main()
