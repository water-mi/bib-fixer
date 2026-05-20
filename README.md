# BibTeX Fixer

A Python GUI tool for reading, editing, and fixing BibTeX files.

## Features

- **Open & edit** `.bib` files with a clear two-pane interface (entry list + field editor)
- **Template alignment** — one-click alignment to standard BibTeX templates (`@article`, `@book`, `@inproceedings`), auto-filling missing fields and removing extras
- **DOI / arXiv fetcher** — paste a DOI or arXiv ID, fetch BibTeX via [doi2bib3](https://github.com/archisman-panigrahi/doi2bib3), and add fields directly to the editor
- **Conference booktitle quick-fill** — pick a conference from `conferences.json` and fill `booktitle` with automatic `{ord}` / `{num}` placeholder resolution
- **Undo / Redo** — Ctrl+Z / Ctrl+Shift+Z in the editor
- **i18n** — Chinese and English UI, switchable from the menu
- **Auto font scaling** — adjusts to window size

## Customization

### `conferences.json`

Defines conference name shortcuts for the `booktitle` quick-fill feature. Two placeholders are supported:

| Placeholder | Meaning | Example |
|-------------|---------|---------|
| `{ord}` | Ordinal number | `21` → `21st` |
| `{num}` | Plain number | `38` → `38` |

```json
{
    "NeurIPS": "Advances in Neural Information Processing Systems {num}",
    "AAAI": "Proceedings of the {ord} AAAI Conference on Artificial Intelligence"
}
```

Edit this file to add your own conferences.

## Run

```bash
# Install dependencies
pip install -r requirements.txt

# Launch
python main.py
```

Requires Python 3.8+ and a desktop environment with tkinter support (`python3-tk` on Debian/Ubuntu).
