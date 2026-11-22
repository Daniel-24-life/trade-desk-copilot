# Trade Desk Copilot

An offline desktop workbench that turns a fictional B2B inquiry into a reviewable reply draft and quote card.

[中文说明](README.zh.md) · [Portfolio](https://github.com/Daniel-24-life/AIfile)

![Quote card rendered from fictional catalog data](assets/screenshots/sample_quotation_card.png)

## What it demonstrates

- Track buyer requirements across turns and keep conversations separate.
- Retrieve catalog evidence, prepare a bilingual draft, and review it before use.
- Render a quote card from the bundled fictional materials.

**Stack** · Python, PyQt5, Markdown catalog, Pillow

## Repository layout

| Path | Contents |
| --- | --- |
| [`app/`](app/) | Desktop interface |
| [`core/`](core/) | Dialogue state, retrieval, draft and card logic |
| [`corpus/`](corpus/) | Synthetic product and company fixtures |
| [`tests/`](tests/) | Offline behavior checks |

## Run locally

```sh
python -m pip install -r requirements.txt
python run_demo.py
python -m pytest tests -q
```


## Scope and limits

The repository uses fictional catalog, company, and inquiry data. It demonstrates offline workflows. Sources, recommendations, and pricing in the demo carry no commercial commitment.
