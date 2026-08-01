# Sample diagrams

The `examples/` directory contains ten valid diagram descriptions. They grow
from an empty document to a platform with multiple actors, services, queues,
databases, branches, joins, and feedback paths.

## Current renderer status

Both CLI format paths were executed for every sample. All 20 commands passed
JSON decoding and schema validation with exit code `0`.

The PlantUML and Excalidraw renderers are not implemented yet. Consequently,
the results below are validation placeholders, not `.puml` or `.excalidraw`
artifacts. The examples are ready to become renderer fixtures in later phases.

## Complexity progression

| # | Sample | Nodes | Edges | New concepts |
| --- | --- | ---: | ---: | --- |
| 1 | [`01-empty-diagram.json`](../examples/01-empty-diagram.json) | 0 | 0 | Smallest valid document and defaults |
| 2 | [`02-single-node.json`](../examples/02-single-node.json) | 1 | 0 | Title and default `generic` node type |
| 3 | [`03-basic-relationship.json`](../examples/03-basic-relationship.json) | 2 | 1 | Actor, service, direction, and labeled edge |
| 4 | [`04-database-flow.json`](../examples/04-database-flow.json) | 3 | 2 | Three-stage request and database flow |
| 5 | [`05-queued-workflow.json`](../examples/05-queued-workflow.json) | 4 | 3 | Queue and asynchronous worker |
| 6 | [`06-service-fan-out.json`](../examples/06-service-fan-out.json) | 5 | 5 | Fan-out, merge, and all-purpose generic node |
| 7 | [`07-event-driven-ordering.json`](../examples/07-event-driven-ordering.json) | 6 | 6 | Event-driven persistence and fulfillment |
| 8 | [`08-microservices-system.json`](../examples/08-microservices-system.json) | 9 | 10 | Gateway fan-out and database-per-service |
| 9 | [`09-resilient-observability-loop.json`](../examples/09-resilient-observability-loop.json) | 11 | 15 | Retry cycle, dead letters, metrics, alerts, and replay |
| 10 | [`10-commerce-platform.json`](../examples/10-commerce-platform.json) | 15 | 22 | Multi-actor commerce platform with synchronous and event-driven paths |

The regression test `tests/test_examples.py` verifies that exactly ten samples
exist, every sample validates, and each successive sample has a larger
`(node count, edge count)` pair.

## Running a sample

With the package installed:

```bash
diagrams-cli examples/04-database-flow.json --format plantuml
diagrams-cli examples/04-database-flow.json --format excalidraw
```

From a source checkout:

```bash
PYTHONPATH=src python -m diagrams_cli examples/04-database-flow.json --format plantuml
PYTHONPATH=src python -m diagrams_cli examples/04-database-flow.json --format excalidraw
```

## Results by output format

| Sample | PlantUML path | Excalidraw path |
| --- | --- | --- |
| 01 — Empty diagram | Exit `0`; accepted, placeholder returned | Exit `0`; accepted, placeholder returned |
| 02 — Single node | Exit `0`; accepted, placeholder returned | Exit `0`; accepted, placeholder returned |
| 03 — Basic relationship | Exit `0`; accepted, placeholder returned | Exit `0`; accepted, placeholder returned |
| 04 — Database flow | Exit `0`; accepted, placeholder returned | Exit `0`; accepted, placeholder returned |
| 05 — Queued workflow | Exit `0`; accepted, placeholder returned | Exit `0`; accepted, placeholder returned |
| 06 — Service fan-out | Exit `0`; accepted, placeholder returned | Exit `0`; accepted, placeholder returned |
| 07 — Event-driven ordering | Exit `0`; accepted, placeholder returned | Exit `0`; accepted, placeholder returned |
| 08 — Microservices system | Exit `0`; accepted, placeholder returned | Exit `0`; accepted, placeholder returned |
| 09 — Resilient observability loop | Exit `0`; accepted, placeholder returned | Exit `0`; accepted, placeholder returned |
| 10 — Commerce platform | Exit `0`; accepted, placeholder returned | Exit `0`; accepted, placeholder returned |

## Recorded CLI output

The following output was recorded by running each JSON file first with
`--format plantuml` and then with `--format excalidraw`:

```text
Placeholder: would generate plantuml from examples/01-empty-diagram.json
Placeholder: would generate excalidraw from examples/01-empty-diagram.json
Placeholder: would generate plantuml from examples/02-single-node.json
Placeholder: would generate excalidraw from examples/02-single-node.json
Placeholder: would generate plantuml from examples/03-basic-relationship.json
Placeholder: would generate excalidraw from examples/03-basic-relationship.json
Placeholder: would generate plantuml from examples/04-database-flow.json
Placeholder: would generate excalidraw from examples/04-database-flow.json
Placeholder: would generate plantuml from examples/05-queued-workflow.json
Placeholder: would generate excalidraw from examples/05-queued-workflow.json
Placeholder: would generate plantuml from examples/06-service-fan-out.json
Placeholder: would generate excalidraw from examples/06-service-fan-out.json
Placeholder: would generate plantuml from examples/07-event-driven-ordering.json
Placeholder: would generate excalidraw from examples/07-event-driven-ordering.json
Placeholder: would generate plantuml from examples/08-microservices-system.json
Placeholder: would generate excalidraw from examples/08-microservices-system.json
Placeholder: would generate plantuml from examples/09-resilient-observability-loop.json
Placeholder: would generate excalidraw from examples/09-resilient-observability-loop.json
Placeholder: would generate plantuml from examples/10-commerce-platform.json
Placeholder: would generate excalidraw from examples/10-commerce-platform.json
```

## Expected use in renderer phases

When rendering is implemented, these inputs should be reused as deterministic
golden fixtures:

- PlantUML runs should produce byte-stable `.puml` text.
- Excalidraw runs should produce byte-stable `.excalidraw` JSON with stable
  element IDs and layout.
- The recorded placeholder section should then be replaced with links to the
  generated artifacts and, where practical, rendered previews.
