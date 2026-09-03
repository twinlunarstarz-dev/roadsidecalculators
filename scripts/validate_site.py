from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/roadsidecalculators/"
errors = []
FORBIDDEN_PUBLIC_COPY = (
    "old version",
    "this version",
    "calculator now",
    "navigation has been rebuilt",
    "updated calculator",
    "accuracy improvement",
)

class Parser(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.title = False
        self.viewport = False
        self.description = False
        self.canonical = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title": self.title = True
        if tag == "meta" and attrs.get("name", "").lower() == "viewport": self.viewport = True
        if tag == "meta" and attrs.get("name", "").lower() == "description" and attrs.get("content", "").strip(): self.description = True
        if tag == "link" and attrs.get("rel", "").lower() == "canonical" and attrs.get("href", "").strip(): self.canonical = True
        for key in ("href", "src"):
            url = attrs.get(key)
            if not url or url.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
                continue
            if url.startswith("/") and not url.startswith(PREFIX):
                errors.append(f"{self.path}: root-relative URL escapes project path: {url}")
                continue
            if url.startswith(PREFIX):
                rel = url[len(PREFIX):].split("?", 1)[0].split("#", 1)[0]
                target = ROOT / rel
                if not rel or rel.endswith("/"):
                    target = target / "index.html"
                if not target.exists():
                    errors.append(f"{self.path}: missing internal target: {url} -> {target.relative_to(ROOT)}")

for path in ROOT.rglob("*.html"):
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    parser = Parser(rel)
    parser.feed(text)
    if not parser.title: errors.append(f"{rel}: missing <title>")
    if not parser.viewport: errors.append(f"{rel}: missing viewport meta")
    if not parser.description: errors.append(f"{rel}: missing meta description")
    if rel.name != "404.html" and not parser.canonical: errors.append(f"{rel}: missing canonical link")
    lower = text.lower()
    for phrase in FORBIDDEN_PUBLIC_COPY:
        if phrase in lower:
            errors.append(f"{rel}: production copy contains implementation/changelog phrase: {phrase!r}")

if errors:
    print("SITE VALIDATION FAILED")
    for error in errors: print("-", error)
    sys.exit(1)
print("Site validation passed: links, metadata, canonicals and production-copy checks succeeded.")
