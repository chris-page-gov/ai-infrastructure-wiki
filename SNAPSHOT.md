# Compatibility snapshot provenance

The original README text, documentation folder and licence files were copied
from `chris-page-gov/okf-explorer` commit `650a928` on 11 July 2026.

The snapshot is deliberately retained at the former repository and Pages URLs
so existing links return content rather than a 404. Current documentation is
maintained at:

<https://github.com/chris-page-gov/okf-explorer/tree/main/docs>

Compatibility-specific landing pages and route mappings are maintained in this
repository. Production corpus data is not duplicated.

`snapshot-files.sha256` records every preserved `README.md` and `docs/` byte.
The compatibility validator rejects changes, removals or unrecorded additions
inside that snapshot. Redirects and moved descriptors therefore live outside
the preserved paths.

The documentation snapshot links to five standards pages, the source-constraint
ledger and one evaluation screenshot that were not included in the initial
compatibility extraction. Those targets are now restored byte-for-byte from
`chris-page-gov/okf-explorer` commit
`650a9285504c2a0dcd189457e142d3f9cef2c842`. Their hashes are recorded
separately in `preserved-routes.sha256`, so the original 40-file
`snapshot-files.sha256` contract remains unchanged.

## Current legislation publications

The compatibility layer maps former and bundle-relative routes to these
canonical paths:

| Resource | Canonical path |
|---|---|
| UK Legislation descriptor | `https://chris-page-gov.github.io/okf-uk-legislation/okf-explorer.json` |
| UK Legislation documentation | `https://chris-page-gov.github.io/okf-uk-legislation/docs/` |
| UK Legislation evaluation | `https://chris-page-gov.github.io/okf-uk-legislation/evaluation/` |
| UK Whole-Law federation | `https://chris-page-gov.github.io/okf-uk-legislation/whole-law/` |
| Whole-Law descriptor | `https://chris-page-gov.github.io/okf-uk-legislation/whole-law/okf-explorer.json` |
| Whole-Law documentation | `https://chris-page-gov.github.io/okf-uk-legislation/whole-law/docs/` |
| Whole-Law evaluation | `https://chris-page-gov.github.io/okf-uk-legislation/whole-law/evaluation/` |

## Current Explorer and government-data publications

| Resource | Canonical path |
|---|---|
| OKF Explorer | `https://chris-page-gov.github.io/okf-explorer/` |
| Explorer registry | `https://chris-page-gov.github.io/okf-explorer/okf-registry.json` |
| UK Government APIs/data discovery | `https://chris-page-gov.github.io/okf-uk-government-apis/` |
| UK Government APIs descriptor | `https://chris-page-gov.github.io/okf-uk-government-apis/okf-explorer.json` |
| Historical full GOV.UK CKAN fixture | `https://chris-page-gov.github.io/ai-engineering-lab-hackathon-london-2026/gov-ckan/okf-explorer.json` |

The historical full CKAN fixture and the current multi-source UK Government
APIs/data discovery publication are not interchangeable. Compatibility routes
retain both destinations and label the distinction.

The complete machine-readable contract is in `compatibility-map.json`.
