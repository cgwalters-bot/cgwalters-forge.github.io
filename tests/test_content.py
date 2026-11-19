"""Check the content tree before zensical build renders it.

Posts are written by agent runs, and the theme inserts front matter into
pages unescaped and lets a page pick its own template, which skips the
policy in overrides/main.html. So content/ may hold only these files, and
each Markdown file's front matter only the keys listed for it, line by line
in source, with values that need no escaping in HTML or YAML.
"""

from pathlib import Path
import re
import tempfile
import unittest

CONTENT = Path(__file__).resolve().parents[1] / "content"

# Copied as they are; Markdown files are rendered with the theme.
STATIC = {"index.html", "robots.txt"}

# Front matter keys, in order, by path pattern.
FRONT_MATTER = {
    r"blog/index\.md": ["title", "description"],
    r"blog/posts/[a-z0-9-]+\.md": ["title", "date"],
}

DATE = r"\d{4}-\d{2}-\d{2}"

# Neither HTML (<>&"') nor YAML (\#, or a leading -?!&*|>%@`) gives these
# characters a meaning; unquoted values have no colon either.
QUOTED = r'"[\w .,:;!?()/-]*"'
PLAIN = r"\w[\w .,;!?()/-]*"


def front_matter_errors(text, keys):
    lines = text.split("\n")
    if lines[0] != "---" or "---" not in lines[1:]:
        return ["front matter is not between --- lines"]
    found = lines[1 : lines.index("---", 1)]
    errors = []
    if [line.split(":", 1)[0] for line in found] != keys:
        errors.append(f"front matter keys are not exactly {keys}, one a line")
    for line in found:
        key, _, value = line.partition(": ")
        pattern = DATE if key == "date" else f"{QUOTED}|{PLAIN}"
        if not re.fullmatch(pattern, value):
            errors.append(f"unsafe or malformed front matter line: {line!r}")
    return errors


def content_errors(root):
    errors = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        name = path.relative_to(root).as_posix()
        if name in STATIC:
            continue
        keys = next(
            (k for p, k in FRONT_MATTER.items() if re.fullmatch(p, name)), None
        )
        if keys is None:
            errors.append(f"{name}: not an expected file; posts are blog/posts/*.md")
            continue
        errors += [f"{name}: {e}" for e in front_matter_errors(path.read_text(), keys)]
    return errors


class ContentTest(unittest.TestCase):
    def test_content(self):
        self.assertEqual(content_errors(CONTENT), [])

    def test_refuses(self):
        post = '---\ntitle: "Weekly notes: week ending 2026-11-01"\ndate: 2026-11-01\n---\n'
        self.assertEqual(front_matter_errors(post, ["title", "date"]), [])
        for bad in [
            '+++\ntitle = "x"\ndate = 2026-11-01\n+++\n',
            '---\ntitle: "x"\ndate: 2026-11-01\ntemplate: base.html\n---\n',
            '---\ntitle: "x"\ndate: 2026-11-01\nauthor: y\n---\n',
            '---\ndate: 2026-11-01\ntitle: "x"\n---\n',
            '---\ntitle: "a \\x3cb"\ndate: 2026-11-01\n---\n',
            '---\ntitle: "<b>"\ndate: 2026-11-01\n---\n',
            '---\ntitle: &a x\ndate: 2026-11-01\n---\n',
            '---\ntitle: a: b\ndate: 2026-11-01\n---\n',
            '---\ntitle: "x"\ndate: 2026-11-01 # c\n---\n',
            '---\ntitle: "x"\n  date: 2026-11-01\n---\n',
            '---\ntitle: "x"\ndate: 2026-11-01\n',
        ]:
            with self.subTest(bad=bad):
                self.assertNotEqual(front_matter_errors(bad, ["title", "date"]), [])

    def test_refuses_paths(self):
        post = '---\ntitle: "x"\ndate: 2026-11-01\n---\n'
        for name in ["blog/2026-11-01.md", "blog/posts/x.html", "x.md", "blog/posts/A.md"]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(post)
                self.assertNotEqual(content_errors(Path(tmp)), [])
