# AGENTS.md

Orientation for agents working in this repo. `CLAUDE.md` (gitignored locally,
not checked in) has the full obsidian-advanced-slides syntax reference —
consult it for slide-authoring syntax; this file is the map, not a duplicate.

## What this repo is

The source of talk material for everything Kemal has presented publicly:
Obsidian decks (2024–2025), Marp decks (2026+, each in its own repo and
submoduled here), and an index (`talks/`) tying together every talk back to
2020, including the ones with no deck in this repo at all.

Company-internal talks live in the sibling private repo, `private-content`
(same layout, not public). See "Relationship to other repos" below.

## Do not move these paths

Three files are linked from live blog pages as GitHub blob URLs, byte-identical
including the URL-encoded spaces. Renaming or moving any of them breaks a
published page:

- `presentations/2025/GopherCon UK 2025 - Unleashing the Go Toolchain.md`
- `media/export/GopherCon UK 2025 - Unleashing the Go Toolchain.pdf`
- `presentations/2024/FOSDEM 2024 - Profiling Python with eBPF - A New Frontier in Performance Analysis.md`

The FOSDEM 2024 path is doubly load-bearing: the blog's `netlify.toml` also
proxies `/notes/*` to an Obsidian-publish site, and the talk's slides link
resolves through that proxy using this same filename. Verify with
`git log --follow <path>` before ever touching one of these.

## Where each kind of content lives

| Path | What's there |
|---|---|
| `presentations/2024/`, `presentations/2025/` | obsidian-advanced-slides decks, edited in this repo |
| `presentations/2026/external/<name>/` | git submodules — one Marp deck repo each, some holding more than one talk |
| `talks/talks.yaml` | source of truth: one entry per talk-at-an-event |
| `talks/INDEX.md` | generated from `talks.yaml` — never hand-edit |
| `scripts/talks.py` | `generate` rewrites INDEX.md; `check` validates talks.yaml |
| `resources/YYYY/<event>/` | research and supporting material per talk |
| `system/templates/`, `system/docs/` | the obsidian-advanced-slides layer: templates, plugin docs |
| `media/` | images, exported PDFs, brand assets |

The canonical **public** index is `kakkoyun.me/categories/talks/` (source:
`kakkoyun/me`, `content/talks/*.md`). This repo's `talks/INDEX.md` is a
cross-reference back to sources, not a replacement for the blog.

## Both toolchains are live

- `presentations/2024|2025/` — obsidian-advanced-slides. Look for
  `<!-- slide template="[[tpl-...]]" -->` directives and YAML frontmatter with
  `duration:`/`theme:`/`highlightTheme:`.
- `presentations/2026/external/*/` — Marp. Look for `marp: true` in the deck's
  frontmatter.

A new Marp deck gets its own repo, scaffolded by the `marp` skill
(`~/src/dotfiles/harness/plugins/research/skills/marp/`), and is then added
here as a submodule — never as a directory of loose files in this repo.

**Never edit inside `presentations/*/external/**`.** Those paths are
submodules: commit changes upstream in the deck's own repo, then bump the
pointer here (`git submodule update --remote <path>` or a manual `git add
<path>` after fetching).

## Adding a talk

1. Edit `talks/talks.yaml` — add one entry per talk-at-an-event (a talk given
   at two events is two entries; a submodule holding two talks is one
   submodule referenced by two entries).
2. Run `uv run scripts/talks.py check` — reports (does not fix) duplicate
   ids, bad dates, dangling paths, and submodules with no matching entry.
3. Run `uv run scripts/talks.py generate` — rewrites `talks/INDEX.md`.
4. Commit `talks.yaml` and `talks/INDEX.md` together.

## Relationship to other repos

- **`kakkoyun/me`** (the blog) is the canonical *public* talks listing. This
  repo holds sources and a cross-reference; it does not replace the blog.
  `talks/talks.yaml` is populated from the blog's `content/talks/*.md` pages,
  not the other way around.
- **`kakkoyun/talks`** is retired — kept public and unarchived with a redirect
  notice pointing at the blog. Do not resurrect it as an index.
- **`private-content`** is the sibling repo for company-internal decks: same
  layout (`AGENTS.md`, `talks/talks.yaml`, `talks/INDEX.md`,
  `presentations/YYYY/external/`, the same `scripts/talks.py`), but private
  and with `visibility: internal` entries. `scripts/talks.py check` refuses
  `visibility: public` inside a repo named `private-content`.

## Known inconsistencies (not regressions — don't "fix" them silently)

- `CLAUDE.md` (gitignored, not in this repo's git history) still documents a
  `posts/` directory that was deleted in commit `92cea31`. If you're editing
  `CLAUDE.md` for other reasons, this is a good time to also drop that line —
  otherwise leave it, it's out of scope for talk consolidation.
- `inspiration/` is gitignored (`.gitignore`: `/inspiration`) despite being
  described in `CLAUDE.md` as reference material. Also out of scope here.

## Follow-up, not implemented

The blog's talks list could eventually be driven from `talks/talks.yaml`
directly — either by making `public-content` a submodule of `kakkoyun/me` plus
a Hugo data-file shim, or a small sync script that emits
`kakkoyun/me/data/talks.yaml`. Not done as part of this consolidation; the
duplication between `talks.yaml` and the blog's `content/talks/*.md` is a
known, deliberate state until someone picks this up.
