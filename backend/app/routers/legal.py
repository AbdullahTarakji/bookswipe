"""Legal endpoints: Privacy Policy and Terms of Service served as HTML."""

import pathlib

import markdown
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/legal", tags=["legal"])

_DOCS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "docs"


def _render_md(filename: str) -> str:
    """Read a markdown file from docs/ and convert to styled HTML."""
    md_path = _DOCS_DIR / filename
    if not md_path.exists():
        return "<h1>Not Found</h1>"
    content = md_path.read_text(encoding="utf-8")
    html_body = markdown.markdown(content, extensions=["tables", "toc"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{filename.replace('.md', '').replace('_', ' ').title()}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #333; }}
  h1 {{ color: #1a1a2e; }} h2 {{ color: #16213e; margin-top: 2em; }}
  a {{ color: #0f3460; }}
</style>
</head>
<body>{html_body}</body>
</html>"""


@router.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy():
    """Serve the privacy policy as HTML."""
    return _render_md("PRIVACY_POLICY.md")


@router.get("/terms", response_class=HTMLResponse)
def terms_of_service():
    """Serve the terms of service as HTML."""
    return _render_md("TERMS_OF_SERVICE.md")
