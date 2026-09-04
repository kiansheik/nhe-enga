# Served Assets

These paths are referenced by source code or documented as public static pages. Keep them present in the `gh-pages` artifact unless the callers are changed.

## Root App

- `/nhe-enga/`: `index.html`
- `/nhe-enga/styles.css`
- `/nhe-enga/manifest.json`
- `/nhe-enga/favicon.ico`
- `/nhe-enga/icon.png`
- `/nhe-enga/js/index.js`
- `/nhe-enga/js/pako.min.js`
- `/nhe-enga/js/papaparse.min.js`
- `/nhe-enga/docs/dict-conjugated.json.gz`
- `/nhe-enga/neologisms.csv`

## Secondary Pages

- `/nhe-enga/quiz/`: `quiz/index.html`, `quiz/quiz.js`, `quiz/styles.css`, `docs/dict-conjugated.json.gz`
- `/nhe-enga/katu/`: `katu/index.html`, `docs/extracted_entries_nheengatu.tar.gz`, shared root CSS/JS
- `/nhe-enga/mbya/`: `mbya/index.html`, `docs/dooley_2006_mbya_dic.json.gz`, shared root CSS/JS
- `/nhe-enga/neologisms/`: `neologisms/index.html`, Google Sheets CSV endpoint
- `/nhe-enga/sentence-builder.html`: `sentence-builder.html`, `docs/dict-conjugated.json`, Pyodide CDN, generated `/nhe-enga/gramatica/pylibs/tupi-0.1.2-py3-none-any.whl`
- `/nhe-enga/translate/`: `translate/index.html`, local Gradio endpoint at `127.0.0.1:7860`; deploy only the HTML page, not local scripts, key files, or logs

## Grammar Site

- `/nhe-enga/gramatica/`: VuePress build output from `gramatica/docs/src`
- `/nhe-enga/gramatica/assets/**`: hashed VuePress JS/CSS/SVG
- `/nhe-enga/gramatica/iframe_pyodide.html`
- `/nhe-enga/gramatica/utility_funcs.js`
- `/nhe-enga/gramatica/pylibs/*.whl` and `*.tar.gz`
- `/nhe-enga/gramatica/favicon.ico`
- `/nhe-enga/gramatica/icon.png`

## Citation Viewer

- `/nhe-enga/docs/primary_sources/`: `docs/primary_sources/index.html`
- `/nhe-enga/docs/primary_sources/vlb/*.png`
- `/nhe-enga/docs/primary_sources/ancharte/*.png`
- `/nhe-enga/docs/primary_sources/arcat1618/*.png`
- `/nhe-enga/docs/primary_sources/betcomp/*.jpg`
- `/nhe-enga/docs/primary_sources/lerhist/*.jpg`
- `/nhe-enga/docs/primary_sources/bettvulg/**`
- `/nhe-enga/docs/primary_sources/cartas_portiguara/**`
