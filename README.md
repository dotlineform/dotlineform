# dotlineform.com (Jekyll site)

This repository is the source for the dotlineform website, built with Jekyll and deployed via GitHub Pages (deploy from `main` / root). The site is served on the custom domain `www.dotlineform.com`.

Primary goals:
- Publish a browsable catalogue of works (stable work IDs, consistent URLs).
- Keep media handling predictable (primaries, thumbnails, attachments).
- Keep catalogue metadata reproducible (generated from a canonical spreadsheet where appropriate).

## Repo structure (high level)

Typical key paths:

- `_works/`  
  Work records (one Markdown file per work ID). Front matter is the canonical metadata for each work page.

- `assets/works/`  
  Site media. Conventionally split by purpose (e.g., images vs files).

- `_layouts/`, `_includes/`, `_sass/`, `assets/`  
  Jekyll layouts, includes, and styling.

- `scripts/`  
  Local helper scripts to generate/update catalogue content and derived images.

## Local development

Requirements:
- Ruby + Bundler (standard Jekyll toolchain)

Install dependencies:

```bash
bundle install
```

Run the site locally:

```bash
bundle exec jekyll serve
```

Then open:
- http://127.0.0.1:4000

## Catalogue model (works)

Works are identified by a stable ID (e.g. `00361`). The site expects:
- a work record in `_works/<id>.md`
- associated images in the expected `assets/` location (including generated thumbnails)

Notes:
- There is no `published` flag in work front matter (the site should not depend on it).
- `catalogue_date` (if present) is for sorting/indexing, not for display on the work page.

## Key scripts (purpose and usage)

The scripts below are intended to be run locally from the repo root. They are designed to keep the catalogue consistent and reduce manual work.

### 1) Generate/update `_works` from the canonical spreadsheet

Purpose:
- Take the canonical “works” spreadsheet export (Excel/CSV) and generate or update `_works/<id>.md`.
- Normalise/coerce fields (types, blanks, formatting) into a stable front matter schema.
- Avoid unnecessary rewrites by computing a deterministic checksum of each work record and skipping unchanged works.

Typical behaviour:
- DRY-RUN mode (show what would change without writing)
- SKIP unchanged works when checksum matches
- WRITE only when a work is new or its checksum differs

Where:
- `scripts/` (Python script; name varies in this repo but the intent is “Excel → Jekyll works generator”)

How to run (pattern):

```bash
python3 scripts/<excel_to_works_script>.py --help
python3 scripts/<excel_to_works_script>.py --dry-run
python3 scripts/<excel_to_works_script>.py
```

What it touches:
- `_works/<id>.md` files only (and optionally logs/manifests if the script produces them)

What to watch:
- If you rename spreadsheet columns (e.g. `artist_display` → `artist`), update the script mapping accordingly.
- If checksums exist in front matter, a matching checksum should always skip writing (even without `--force`).

### 2) Generate thumbnails for works images

Purpose:
- Create small, fast thumbnails for indexes and grids.
- Maintain consistent naming and sizes (e.g. 96px and 192px WebP), with centre-crop or fit strategy as defined by the script.
- Ensure output is deterministic and repeatable.

Where:
- `scripts/make_work_images.sh` (or similarly named image helper script)

Typical output:
- Writes derived thumbnails into a predictable location (commonly alongside work images, or a `thumbs/` subfolder).
- Example filenames:
  - `<id>-thumb-96.webp`
  - `<id>-thumb-192.webp`

How to run:

```bash
bash scripts/make_work_images.sh
```

What it depends on:
- Usually `ffmpeg` for WebP encoding and scaling/cropping.

## Deployment (GitHub Pages)

Publishing mode:
- Deploy from branch: `main`
- Folder: `/` (root)

Custom domain:
- `www.dotlineform.com`

Operational notes:
- Renaming the repository does not break the custom domain as long as:
  1) the custom domain remains set in Settings → Pages for the renamed repo, and
  2) DNS still points `www` to GitHub Pages (typically via CNAME to `dotlineform.github.io`).

## Conventions

- Filenames: prefer stable, ASCII-safe names.
- Work IDs: fixed-width numeric strings (e.g. `00361`), used consistently in filenames and paths.
- Attachments: stored under a work-specific path with non-derived filenames.

## Working on this repo

Suggested workflow:
1) Update canonical metadata (spreadsheet)
2) Run the works generator script (dry-run first)
3) Generate thumbnails/derived images if needed
4) Run site locally
5) Commit and push
