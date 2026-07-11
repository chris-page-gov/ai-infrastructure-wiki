# AI Infrastructure Wiki compatibility publication

This repository preserves the former public URLs of
`chris-page-gov/ai-infrastructure-wiki` following its rename to
[`chris-page-gov/okf-explorer`](https://github.com/chris-page-gov/okf-explorer)
and the extraction of production OKF bundles into independently versioned
repositories.

Human-facing routes redirect while preserving query strings and fragments.
Former JSON bundle descriptor routes serve the minimal machine-readable
`okf-moved.v1` contract:

```json
{
  "schema": "okf-moved.v1",
  "kind": "okf-moved",
  "moved_to": "https://canonical.example/okf-explorer.json"
}
```

OKF Explorer v0.4.0 and later follows this contract transparently. This is a
deprecation-cycle compatibility layer, not a copy of any production corpus.

## Canonical publications

- Explorer: <https://chris-page-gov.github.io/okf-explorer/>
- AI Infrastructure: <https://chris-page-gov.github.io/okf-ai-infrastructure/>
- UK Government APIs: <https://chris-page-gov.github.io/okf-uk-government-apis/>
- UK Legislation: <https://chris-page-gov.github.io/okf-uk-legislation/>

Decision date: 11 July 2026.
