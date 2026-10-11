# Data-Layer Interoperability Checker

Describe your martech stack (CDP, ad platforms, analytics, CRM, email, attribution) and the identifiers each tool uses. Get an **Identity Fragmentation Score** (0 = unified, 100 = fully fragmented), a list of specific problems, and a graph of which tools can actually be joined.

- **Browser demo:** open `web/index.html` (no build, works offline). Three example stacks load with one click.
- **CLI:** `PYTHONPATH=src python3 -m interop_checker examples/lean_ecommerce.json`
- **Library:** `from interop_checker import analyze`

## How the score works
Tools are nodes. Two tools are linked if they share at least one identifier (email hash, cookie ID, device ID, phone, CRM contact ID, IP). Score = disconnected clusters (up to 50) + isolated tools (up to 30) + missing identity hub (0, 10 or 20), rounded like JavaScript. Bands: 0-25 low, 26-50 moderate, 51-75 high, 76-100 severe.

Flags: isolated tool, web-tracking tools with no shared identifier, CDP that is not connected to everything, no identity owner, split clusters, many identifier schemes with no single key, CRM/email not connected to ad platforms.

## Evaluation
`python3 -m unittest discover -s tests` and `python3 eval/run_eval.py` (full table in `eval/results.md`).

| Check | Result |
|---|---|
| Unit tests | 10 pass, including the three example scores (0, 37, 29) recorded from the original Node run |
| Planted defects, 100 stacks each (isolate a tool, split into clusters, demote the CDP, cut CRM from ads) | **100/100 detected** for each; the right tool was named 100/100 in the isolation case |
| False alarms on 100 clean stacks | **0/100** for every flag |
| Score never drops when a defect is planted | 100/100 in every case |

## A bug the eval found
The first version of this eval showed 12 false alarms on clean stacks. Cause: the "CRM/email not connected to ad platforms" rule required a **direct** shared identifier and ignored a path through the CDP. The original demo's own enterprise example (score 0, "Segment connects to every other tool") also showed that critical flag, which contradicts itself. The rule now asks whether the two sides are in the same connected cluster. Fixed in `web/index.html` and the Python port; the enterprise example is a regression test.

## Limits
- Self-reported identifiers, not observed data. A shared identifier name does not mean records actually join: match rates can be 20% or 95%.
- Rule-based and synthetic evals. Detection near 100% is expected; the value is regression protection and a measured false-alarm rate.
- Identifier set is fixed to six types.

## Next step
Audit two real stacks by measuring join rates between systems, and compare the score with the measured rate.
