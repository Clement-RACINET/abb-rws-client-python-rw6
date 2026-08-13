#!/usr/bin/env python3
"""Generate documentation artifacts for CI.

This script is kept as a compatibility wrapper for the GitHub Actions workflow.
The actual documentation generation is delegated to py-doc-tools.
"""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Run py-doc-tools documentation generation."""
    result = subprocess.run(
        [sys.executable, "-m", "py_doc_tools", "generate", "--all"],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
