> This text is LLM generated.

# cgwalters-forge.github.io

The organization site at <https://cgwalters-forge.github.io/>: a hand-written homepage describing how the first-party projects fit together, extending the organization README, and the weekly notes at `/blog/`. It is built with [Zensical](https://zensical.org/) (`zensical.toml`) and deployed to GitHub Pages by `.github/workflows/site.yml`, which also builds every pull request and checks its internal links with [lychee](https://lychee.cli.rs/).

The homepage is not a list of repositories; GitHub already shows those. Update it, `content/index.html`, when the architecture changes; it is plain HTML with its own styles, copied as it is. To preview locally, install Zensical from `site-requirements.txt` into a virtual environment and run `zensical serve`; before pushing, run `zensical build --strict` and the lychee command `site.yml` runs, with the versions it pins.

## Adding a post

A post is one Markdown file, `content/blog/posts/YYYY-MM-DD.md`, served at `/blog/YYYY-MM-DD/`, with a title and date in its YAML front matter:

```markdown
---
title: "Week ending 2026-11-01"
date: 2026-11-01
---

The post, in Markdown.
```

Posts are Markdown only: CI fails on raw HTML (a tag, comment or `<script>` outside code), since the posts are written by agent runs and served on an origin other pages trust. The blog index lists posts newest first, and `/blog/atom.xml` is their feed (RSS 2.0, at the URL the Zola site used for Atom). Every pull request here gets the organization's agent review (`.github/workflows/review.yml`, with its task in `workflow/review.md`), which for a post checks it against the issue's material and refuses raw HTML or anything that must not be published. Each Sunday, tracker's `weekly-blog.yml` files an issue here with the week's material and dispatches a run that writes the post as a pull request.
