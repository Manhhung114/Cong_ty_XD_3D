"""Build a self-contained HTML front-end for Streamlit's static file hosting.

Streamlit versions may serve .js or .css with a restricted MIME type, which
prevents ES modules from loading. Bundle public JS modules and CSS inside HTML.
Do not embed private documents, API keys or backend code.
"""
from __future__ import annotations

import base64
import os
import re
from pathlib import Path

IMPORT = re.compile(r"\bfrom\s+(['\"])(\.{1,2}/[^'\"\n]+\.js)\1")
CSS_LINK = re.compile(r'<link\s+rel="stylesheet"\s+href="\./([^"<>]+\.css)"\s*/?>')
ENTRY = re.compile(r'<script\s+type="module"\s+src="\./src/app\.js"\s*></script>')
ASSET = re.compile(r"(['\"])(\./assets/[^'\"\n]+\.(?:webp|png|jpg|jpeg|svg))\1")


def build(static: Path, destination: str = "standalone.html") -> Path:
    static = Path(static).resolve()
    page = static / "index.html"
    target = static / destination
    cache: dict[Path, str] = {}
    visiting: set[Path] = set()

    def safe(path: Path) -> Path:
        path = path.resolve()
        if not path.is_relative_to(static):
            raise ValueError(f"Asset outside public directory: {path}")
        return path

    def encoded_module(file: Path) -> str:
        file = safe(file)
        if file in cache:
            return cache[file]
        if file in visiting:
            raise ValueError(f"Circular module import: {file}")
        visiting.add(file)
        source = file.read_text(encoding="utf-8")

        def asset(match: re.Match[str]) -> str:
            image = safe(static / match.group(2).lstrip("./"))
            suffix = image.suffix.lower().lstrip(".")
            mime = {"svg": "image/svg+xml", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}[suffix]
            return match.group(1) + f"data:{mime};base64," + base64.b64encode(image.read_bytes()).decode("ascii") + match.group(1)

        source = ASSET.sub(asset, source)

        def sub_import(match: re.Match[str]) -> str:
            dep = safe(file.parent / match.group(2))
            return "from '" + encoded_module(dep) + "'"

        source = IMPORT.sub(sub_import, source)
        visiting.remove(file)
        encoded = "data:text/javascript;base64," + base64.b64encode(source.encode("utf-8")).decode("ascii")
        cache[file] = encoded
        return encoded

    html = page.read_text(encoding="utf-8")

    def inline_css(match: re.Match[str]) -> str:
        css = safe(static / match.group(1)).read_text(encoding="utf-8")
        return "<style>\n" + css.replace("</style>", "<\\/style>") + "\n</style>"

    html, css_count = CSS_LINK.subn(inline_css, html)
    entry_url = encoded_module(static / "src/app.js")
    html, entry_count = ENTRY.subn(lambda _: f'<script type="module" src="{entry_url}"></script>', html)
    if not entry_count or not css_count:
        raise ValueError(f"Missing entry/CSS in HTML: {entry_count=} {css_count=}")
    if re.search(r'<script[^>]+src="\./src/', html):
        raise ValueError("External script survived bundling")
    if '__previewData' in html or '__localStore' in html:
        raise ValueError("Preview-only mocks must not be shipped")
    staged = target.with_suffix(".tmp")
    if target.is_file() and target.read_text(encoding="utf-8") == html:
        return target
    staged.write_text(html, encoding="utf-8")
    os.replace(staged, target)
    return target


if __name__ == "__main__":
    import sys
    print(build(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "static"))
