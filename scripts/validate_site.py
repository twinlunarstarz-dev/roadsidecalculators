from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/roadsidecalculators/"
errors = []

class Parser(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.title = False
        self.viewport = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title": self.title = True
        if tag == "meta" and attrs.get("name", "").lower() == "viewport": self.viewport = True
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
    parser = Parser(path.relative_to(ROOT))
    parser.feed(path.read_text(encoding="utf-8"))
    if not parser.title:
        errors.append(f"{path.relative_to(ROOT)}: missing <title>")
    if not parser.viewport:
        errors.append(f"{path.relative_to(ROOT)}: missing viewport meta")

if errors:
    print("SITE VALIDATION FAILED")
    for error in errors:
        print("-", error)
    sys.exit(1)
print("Site validation passed: internal project-path links and assets resolve.")
