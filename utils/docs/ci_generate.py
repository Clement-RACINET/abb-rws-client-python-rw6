#!/usr/bin/env python3
import sys

sys.path.insert(0, '.')
from utils.docs.config import build_config
from utils.docs.generate_api import generate_api_docs, update_mkdocs_nav

cfg = build_config()
nav = generate_api_docs(cfg)
update_mkdocs_nav(cfg, nav)
