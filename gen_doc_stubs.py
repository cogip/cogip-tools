#!/usr/bin/env python
from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

src_root = Path("cogip")
for path in sorted(src_root.glob("**/*.py")):
    if path.stem.endswith("_pb2"):
        continue
    if path.stem == "__init__":
        continue
    module_path = path.with_suffix("")
    doc_path = module_path.with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    nav[module_path.parts] = doc_path

    with mkdocs_gen_files.open(full_doc_path, "w") as f:
        ident = ".".join(module_path.parts)
        print("::: " + ident, file=f)

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
