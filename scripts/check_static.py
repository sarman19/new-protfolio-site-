 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/scripts/check_static.py b/scripts/check_static.py
new file mode 100644
index 0000000000000000000000000000000000000000..a40044e56ba178ee0564b7405e967d6e8d780e86
--- /dev/null
+++ b/scripts/check_static.py
@@ -0,0 +1,45 @@
+from html.parser import HTMLParser
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[1]
+index = ROOT / "index.html"
+css = ROOT / "src" / "styles.css"
+
+class LinkCollector(HTMLParser):
+    def __init__(self):
+        super().__init__()
+        self.ids = set()
+        self.hrefs = []
+        self.title_seen = False
+
+    def handle_starttag(self, tag, attrs):
+        attr_map = dict(attrs)
+        if "id" in attr_map:
+            self.ids.add(attr_map["id"])
+        if tag == "a" and "href" in attr_map:
+            self.hrefs.append(attr_map["href"])
+        if tag == "title":
+            self.title_seen = True
+
+html = index.read_text(encoding="utf-8")
+styles = css.read_text(encoding="utf-8")
+parser = LinkCollector()
+parser.feed(html)
+
+required_sections = {"home", "about", "contact", "work", "case-study"}
+missing = required_sections - parser.ids
+if missing:
+    raise SystemExit(f"Missing required sections: {', '.join(sorted(missing))}")
+
+broken_hashes = sorted(
+    href for href in parser.hrefs if href.startswith("#") and href != "#" and href[1:] not in parser.ids
+)
+if broken_hashes:
+    raise SystemExit(f"Broken in-page links: {', '.join(broken_hashes)}")
+
+required_css_tokens = [".hero", ".marquee", ".service-card", ".testimonial-card", ".project-row", "@media"]
+missing_css = [token for token in required_css_tokens if token not in styles]
+if missing_css:
+    raise SystemExit(f"Missing CSS blocks: {', '.join(missing_css)}")
+
+print("Static portfolio checks passed.")
 
EOF
)
