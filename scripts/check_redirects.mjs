#!/usr/bin/env node
/**
 * Execute the deployed 404 redirect script against the compatibility route
 * matrix. This tests the real browser code rather than a duplicate resolver.
 */

import { readFileSync } from "node:fs";
import vm from "node:vm";

const root = new URL("../", import.meta.url);
const mapping = JSON.parse(
  readFileSync(new URL("compatibility-map.json", root), "utf8"),
);

function extractScript(relative) {
  const html = readFileSync(new URL(relative, root), "utf8");
  const match = html.match(/<script>([\s\S]*?)<\/script>/);
  if (!match) {
    throw new Error(`${relative} does not contain a redirect script`);
  }
  return match[1];
}

const fallbackScript = extractScript("404.html");
const cases = [
  [
    "/ai-infrastructure-wiki/evaluation/legislation/questions.json",
    "https://chris-page-gov.github.io/okf-uk-legislation/evaluation/questions.json?run=1#case",
  ],
  [
    "/legislation/evaluation/answer-schema.json",
    "https://chris-page-gov.github.io/okf-uk-legislation/evaluation/answer-schema.json?run=1#case",
  ],
  [
    "/legislation/docs/index.md",
    "https://chris-page-gov.github.io/okf-uk-legislation/docs/index.md?run=1#case",
  ],
  [
    "/docs/uk-legislation/getting-started.md",
    "https://chris-page-gov.github.io/okf-uk-legislation/docs/getting-started.md?run=1#case",
  ],
  [
    "/whole-law/okf-explorer.json",
    "https://chris-page-gov.github.io/okf-uk-legislation/whole-law/okf-explorer.json?run=1#case",
  ],
  [
    "/whole-law/evaluation/questions.json",
    "https://chris-page-gov.github.io/okf-uk-legislation/whole-law/evaluation/questions.json?run=1#case",
  ],
  [
    "/ai-infrastructure-wiki/evaluation/whole-law/answer-schema.json",
    "https://chris-page-gov.github.io/okf-uk-legislation/whole-law/evaluation/answer-schema.json?run=1#case",
  ],
  [
    "/data-gov-uk/okf-explorer.json",
    "https://chris-page-gov.github.io/okf-uk-government-apis/okf-explorer.json?run=1#case",
  ],
  [
    "/data.gov.uk/data/manifest.json",
    "https://chris-page-gov.github.io/okf-uk-government-apis/data/manifest.json?run=1#case",
  ],
  [
    "/docs/not-in-snapshot.md",
    "https://github.com/chris-page-gov/okf-explorer/blob/main/docs/not-in-snapshot.md?run=1#case",
  ],
  [
    "/gov-ckan/okf-explorer.json",
    "https://chris-page-gov.github.io/ai-engineering-lab-hackathon-london-2026/gov-ckan/okf-explorer.json?run=1#case",
  ],
  [
    "/legislation/data/manifest.json",
    "https://chris-page-gov.github.io/okf-uk-legislation/data/manifest.json?run=1#case",
  ],
  [
    "/uk-government-apis/okf-explorer.json",
    "https://chris-page-gov.github.io/okf-uk-government-apis/okf-explorer.json?run=1#case",
  ],
  [
    "/evaluation/gov-ckan/questions.json",
    "https://chris-page-gov.github.io/okf-explorer/evaluation/gov-ckan/questions.json?run=1#case",
  ],
  [
    "/evaluation/okf-explorer/questions.json",
    "https://chris-page-gov.github.io/okf-explorer/evaluation/okf-explorer/questions.json?run=1#case",
  ],
  [
    "/okf-registry.json",
    "https://chris-page-gov.github.io/okf-explorer/okf-registry.json?run=1#case",
  ],
  [
    "/stack/example",
    "https://chris-page-gov.github.io/okf-ai-infrastructure/stack/example?run=1#case",
  ],
  [
    "/standards/arazzo.md",
    "https://chris-page-gov.github.io/okf-ai-infrastructure/standards/arazzo.md?run=1#case",
  ],
  [
    "/uk-government/gds-api-standards.md",
    "https://chris-page-gov.github.io/okf-ai-infrastructure/uk-government/gds-api-standards.md?run=1#case",
  ],
  [
    "/stack/observability-and-provenance.md",
    "https://chris-page-gov.github.io/okf-ai-infrastructure/stack/observability-and-provenance.md?run=1#case",
  ],
  [
    "/glossary/provenance.md",
    "https://chris-page-gov.github.io/okf-ai-infrastructure/glossary/provenance.md?run=1#case",
  ],
  [
    "/unknown/path",
    "https://chris-page-gov.github.io/okf-explorer/unknown/path?run=1#case",
  ],
];

const failures = [];
for (const [pathname, expected] of cases) {
  let actual;
  const location = {
    pathname,
    search: "?run=1",
    hash: "#case",
    replace(value) {
      actual = value;
    },
  };
  vm.runInNewContext(fallbackScript, { location }, { filename: "404.html" });
  if (actual !== expected) {
    failures.push(`${pathname}: expected ${expected}, got ${actual}`);
  }
}

for (const [relative, target] of Object.entries(mapping.static_redirects)) {
  let actual;
  const location = {
    pathname: `/${relative.replace(/index\.html$/, "")}`,
    search: "?run=1",
    hash: "#case",
    replace(value) {
      actual = value;
    },
  };
  vm.runInNewContext(
    extractScript(relative),
    { location, URLSearchParams },
    { filename: relative },
  );
  const separator = target.includes("?") ? "&" : "?";
  const expected = `${target}${separator}run=1#case`;
  if (actual !== expected) {
    failures.push(`${relative}: expected ${expected}, got ${actual}`);
  }
}

{
  let actual;
  const location = {
    pathname: "/gov-ckan/",
    search: "?bundle=https%3A%2F%2Fevil.example%2Fbundle.json&view=graph&run=1",
    hash: "#case",
    replace(value) {
      actual = value;
    },
  };
  vm.runInNewContext(
    extractScript("gov-ckan/index.html"),
    { location, URLSearchParams },
    { filename: "gov-ckan/index.html" },
  );
  const expected =
    "https://chris-page-gov.github.io/okf-explorer/" +
    "?bundle=https%3A%2F%2Fchris-page-gov.github.io%2Fai-engineering-lab-hackathon-london-2026%2Fgov-ckan%2Fokf-explorer.json" +
    "&view=graph&run=1#case";
  if (actual !== expected) {
    failures.push(
      `gov-ckan fixed bundle: expected ${expected}, got ${actual}`,
    );
  }
}

if (failures.length) {
  throw new Error(`redirect validation failed:\n- ${failures.join("\n- ")}`);
}

console.log(
  "redirect validation passed: " +
    `${cases.length} fallback routes, ` +
    `${Object.keys(mapping.static_redirects).length} static redirects, ` +
    "and fixed CKAN bundle enforcement",
);
