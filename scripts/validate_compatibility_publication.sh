#!/bin/sh
set -eu

python3 -m json.tool okf-bundle.json >/dev/null
python3 -m json.tool okf-bundle.jsonld >/dev/null
python3 -m json.tool okf-explorer.json >/dev/null
python3 -m json.tool legislation/okf-explorer.json >/dev/null
python3 -m json.tool legislation/okf-bundle.jsonld >/dev/null
python3 -m json.tool uk-government-apis/okf-explorer.json >/dev/null
python3 -m json.tool uk-government-apis/okf-bundle.jsonld >/dev/null
python3 -m json.tool gov-ckan/okf-explorer.json >/dev/null
python3 -m json.tool compatibility-map.json >/dev/null
python3 -m json.tool evaluation/legislation/answer-schema.json >/dev/null
python3 -m json.tool evaluation/legislation/questions.json >/dev/null
python3 -m json.tool whole-law/okf-explorer.json >/dev/null
python3 -m json.tool whole-law/okf-bundle.jsonld >/dev/null
python3 -m json.tool whole-law/evaluation/answer-schema.json >/dev/null
python3 -m json.tool whole-law/evaluation/questions.json >/dev/null
grep -q 'okf-moved.v1' README.md
grep -q 'location.replace' index.html
grep -q 'okf-uk-legislation' 404.html
grep -q 'okf-uk-government-apis' 404.html
python3 scripts/check_compatibility.py
python3 scripts/test_internal_links.py
python3 scripts/check_internal_links.py
python3 scripts/build_sbom.py --check
python3 scripts/test_workflow_contract.py
node scripts/check_redirects.mjs
