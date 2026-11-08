"""Check homepage navigation after running zola build."""

from html.parser import HTMLParser
from pathlib import Path
import unittest


class NavigationParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_nav = False
        self.href = None
        self.text = ""
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "nav":
            self.in_nav = True
        elif tag == "a" and self.in_nav:
            self.href = dict(attrs).get("href")
            self.text = ""

    def handle_data(self, data):
        if self.href is not None:
            self.text += data

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_nav = False
        elif tag == "a" and self.href is not None:
            self.links.append((self.href, self.text.strip()))
            self.href = None


class HomeNavigationTest(unittest.TestCase):
    def test_navigation_destinations(self):
        public = Path(__file__).resolve().parents[1] / "public"
        parser = NavigationParser()
        parser.feed((public / "index.html").read_text())
        self.assertIn(
            ("https://cgwalters-forge.github.io/review/", "Control app"),
            parser.links,
        )
        self.assertIn(("/blog/", "Blog"), parser.links)
        self.assertTrue((public / "blog/index.html").is_file())
