from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "index.html", ROOT / "work.html", ROOT / "contact.html"]
CSS = ROOT / "src" / "styles.css"


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []
        self.stylesheets = []
        self.title_seen = False
        self._inside_title = False

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        if "id" in attr_map:
            self.ids.add(attr_map["id"])
        if tag == "a" and "href" in attr_map:
            self.hrefs.append(attr_map["href"])
        if tag == "link" and attr_map.get("rel") == "stylesheet":
            self.stylesheets.append(attr_map.get("href", ""))
        if tag == "title":
            self._inside_title = True

    def handle_data(self, data):
        if self._inside_title and data.strip():
            self.title_seen = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._inside_title = False


def parse_page(path):
    parser = LinkCollector()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


for path in PAGES:
    if not path.exists():
        raise SystemExit(f"Missing page: {path.relative_to(ROOT)}")

page_data = {path.name: parse_page(path) for path in PAGES}
all_ids = {name: data.ids for name, data in page_data.items()}

required_sections = {
    "index.html": {"home", "about", "reviews"},
    "work.html": {"case-study", "pixelend", "interior", "finance", "reviews"},
    "contact.html": {"contact"},
}
for page, required in required_sections.items():
    missing = required - all_ids[page]
    if missing:
        raise SystemExit(f"{page} missing required sections: {', '.join(sorted(missing))}")
    if not page_data[page].title_seen:
        raise SystemExit(f"{page} is missing a title")
    if "src/styles.css" not in page_data[page].stylesheets:
        raise SystemExit(f"{page} does not load src/styles.css")

for page, data in page_data.items():
    for href in data.hrefs:
        parsed = urlparse(href)
        if parsed.scheme in {"http", "https", "mailto"}:
            continue
        target_page = parsed.path or page
        if target_page.startswith("/"):
            target_page = target_page.lstrip("/")
        if target_page and not (ROOT / target_page).exists():
            raise SystemExit(f"{page} links to missing page: {href}")
        if parsed.fragment:
            page_name = Path(target_page or page).name
            if parsed.fragment not in all_ids.get(page_name, set()):
                raise SystemExit(f"{page} links to missing section: {href}")

styles = CSS.read_text(encoding="utf-8")
required_css_tokens = [
    ".hero",
    ".marquee",
    ".service-card",
    ".testimonial-card",
    ".project-row",
    ".case-card",
    ".contact-card",
    "@media",
]
missing_css = [token for token in required_css_tokens if token not in styles]
if missing_css:
    raise SystemExit(f"Missing CSS blocks: {', '.join(missing_css)}")

print("Static portfolio checks passed.")
