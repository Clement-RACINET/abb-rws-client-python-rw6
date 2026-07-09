# contrib/docs/config.py  (adapté pour abb_rws_client)
def build_config() -> DocConfig:
    return DocConfig(
        project_root    = PROJECT_ROOT,
        mkdocs_path     = PROJECT_ROOT / "mkdocs.yml",
        docs_src_dir    = PROJECT_ROOT / "docs",
        docs_api_dir    = PROJECT_ROOT / "docs" / "api",
        packages_to_scan = ["abb_rws_client"],   # ← seul changement
        exclude_dirs    = {
            "__pycache__", ".pytest_cache", ".git", ".pixi",
            "abb_rws_client.egg-info",
        },
        exclude_files   = ["__init__.py", "test_*.py"],
    )