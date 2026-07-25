#!/usr/bin/env node
/**
 * Execute the deployed 404 redirect script against the compatibility route
 * matrix. This tests the real browser code rather than a duplicate resolver.
 */

import { readFileSync } from "node:fs";
import vm from "node:vm";

const html = readFileSync(new URL("../404.html", import.meta.url), "utf8");
const match = html.match(/<script>([\s\S]*?)<\/script>/);
if (!match) {
  throw new Error("404.html does not contain a redirect script");
}

const script = match[1];
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
    "/stack/example",
    "https://chris-page-gov.github.io/okf-ai-infrastructure/stack/example?run=1#case",
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
  vm.runInNewContext(script, { location }, { filename: "404.html" });
  if (actual !== expected) {
    failures.push(`${pathname}: expected ${expected}, got ${actual}`);
  }
}

if (failures.length) {
  throw new Error(`redirect validation failed:\n- ${failures.join("\n- ")}`);
}

console.log(`redirect validation passed: ${cases.length} browser routes`);
