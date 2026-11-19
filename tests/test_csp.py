"""Check the built pages' scripts against their policy after zensical build.

CI runs this before it uploads the Pages artifact.
"""

from base64 import b64encode
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

CSP = "content-security-policy"

# The policy overrides/main.html sets, by directive.
DIRECTIVES = {"object-src", "base-uri", "script-src"}

# The only script a page may load: the theme's bundle, relative or rooted.
BUNDLE = r"/?(\.\./)*assets/javascripts/bundle\.[0-9a-f]+\.min\.js"

SOURCE_ATTRS = ("src", "href", "xlink:href")

# The hand-written homepage, which has no policy and so may have no script.
HOME = "index.html"


class ScriptParser(HTMLParser):
    """Collects the policy, and each script in order, noting what came first."""

    def __init__(self):
        super().__init__()
        self.policy = None
        self.policy_first = False
        self.seen_other = False
        self.script = None
        self.inline = []
        self.sources = []
        self.count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and (attrs.get("http-equiv") or "").lower() == CSP:
            self.policy = attrs.get("content")
            self.policy_first = not self.seen_other
            return
        if tag not in ("html", "head", "meta"):
            self.seen_other = True
        if tag == "script":
            self.count += 1
        # SVG's script element loads its file from href.
        source = next((attrs[k] for k in SOURCE_ATTRS if k in attrs), None)
        if tag == "script" and source is not None:
            self.sources.append(source)
        # JSON data blocks are never run.
        elif (
            tag == "script"
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
    def test_scripts_are_allowed_by_policy(self):
        public = Path(__file__).resolve().parents[1] / "public"
        pages = sorted(public.rglob("*.html"))
        self.assertGreater(len(pages), 3)
        # One policy, main.html's, on every themed page.
        policies = set()
        for page in pages:
            name = page.relative_to(public).as_posix()
            with self.subTest(page=name):
                parser = ScriptParser()
                parser.feed(page.read_text())
                if name == HOME:
                    self.assertEqual(parser.count, 0)
                    continue
                self.assertIsNotNone(parser.policy)
                self.assertTrue(parser.policy_first)
                policies.add(parser.policy)
                self.assertEqual(len(policies), 1)
                sources = {}
                for directive in parser.policy.split(";"):
                    key, *values = directive.split()
                    sources[key] = values
                self.assertEqual(set(sources), DIRECTIVES)
                for script in parser.inline:
                    digest = b64encode(sha256(script.encode()).digest()).decode()
                    self.assertIn(f"'sha256-{digest}'", sources["script-src"])
                for source in sources["script-src"]:
                    self.assertTrue(
                        source == "'self'" or re.fullmatch(r"'sha256-[A-Za-z0-9+/]+=*'", source),
                        source,
                    )
                for source in parser.sources:
                    self.assertRegex(source, f"^{BUNDLE}$")
