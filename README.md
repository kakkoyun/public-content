# public-content

Information about all my public appearances past, present and future.

Slides are made with: https://mszturc.github.io/obsidian-advanced-slides

## Where to find things

| Path | What's there |
|---|---|
| `presentations/YYYY/` (2024, 2025) | obsidian-advanced-slides decks, edited directly in this repo |
| `presentations/2026/external/<name>/` | git submodules — Marp deck repos, one per submodule (some hold more than one talk) |
| `talks/talks.yaml` | source of truth — edit here to add or update a talk |
| `talks/INDEX.md` | generated index, entry point for browsing — do not hand-edit |
| `resources/YYYY/<event>/` | research and supporting material per talk |
| `system/templates/`, `system/docs/` | the obsidian-advanced-slides layer: templates and plugin docs |

The canonical **public** talks listing is
[kakkoyun.me/categories/talks/](https://kakkoyun.me/categories/talks/). This
repo holds the underlying sources and a cross-reference index, not a
replacement.

Company-internal decks live in the sibling private repo, `private-content`.

Clone with submodules:

```bash
git clone --recurse-submodules git@github.com:kakkoyun/public-content.git
# already cloned:
git submodule update --init --recursive
```

See `AGENTS.md` for the do-not-move constraints and the full agent-oriented map.
