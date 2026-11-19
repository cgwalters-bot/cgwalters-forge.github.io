"""Check the built blog pages' scripts against their policy after zensical build."""

from base64 import b64encode
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import unittest

CSP = "content-security-policy"


class ScriptParser(HTMLParser):
    """Collects the policy, and each script in order, noting what came first."""

    def __init__(self):
        super().__init__()
        self.policy = None
        self.policy_first = False
        self.seen_other = False
        self.script = None
        self.inline = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and (attrs.get("http-equiv") or "").lower() == CSP:
            self.policy = attrs.get("content")
            self.policy_first = not self.seen_other
            return
        if tag not in ("html", "head", "meta"):
            self.seen_other = True
        # JSON data blocks are never run.
        if (
            tag == "script"
            and "src" not in attrs
            and attrs.get("type") in (None, "", "text/javascript", "module")
        ):
            self.script = ""

    def handle_data(self, data):
        if self.script is not None:
            self.script += data

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            self.inline.append(self.script)
            self.script = None


class CspTest(unittest.TestCase):
    def test_inline_scripts_are_allowed_by_hash(self):
        public = Path(__file__).resolve().parents[1] / "public"
        pages = [public / "404.html", *(public / "blog").rglob("*.html")]
        self.assertGreater(len(pages), 2)
        for page in pages:
            with self.subTest(page=str(page.relative_to(public))):
                parser = ScriptParser()
                parser.feed(page.read_text())
                self.assertIsNotNone(parser.policy)
                self.assertTrue(parser.policy_first)
                sources = {}
                for directive in parser.policy.split(";"):
                    name, *values = directive.split()
                    sources[name] = values
                self.assertNotIn("'unsafe-inline'", sources["script-src"])
                for script in parser.inline:
                    digest = b64encode(sha256(script.encode()).digest()).decode()
                    self.assertIn(f"'sha256-{digest}'", sources["script-src"])
