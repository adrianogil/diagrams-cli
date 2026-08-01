# Sample diagrams

The `examples/` directory contains ten valid diagram descriptions. They grow
from an empty document to a platform with multiple actors, services, queues,
databases, branches, joins, and feedback paths.

## Current renderer status

Both CLI format paths were executed for every sample. Every PlantUML result is
checked in under `examples/plantuml/`, and every editable Excalidraw result is
checked in under `examples/excalidraw/`.

## Complexity progression

| # | Sample | Nodes | Edges | PlantUML | Excalidraw | New concepts |
| --- | --- | ---: | ---: | --- | --- | --- |
| 1 | [`01-empty-diagram.json`](../examples/01-empty-diagram.json) | 0 | 0 | [`puml`](../examples/plantuml/01-empty-diagram.puml) | [`excalidraw`](../examples/excalidraw/01-empty-diagram.excalidraw) | Smallest valid document and defaults |
| 2 | [`02-single-node.json`](../examples/02-single-node.json) | 1 | 0 | [`puml`](../examples/plantuml/02-single-node.puml) | [`excalidraw`](../examples/excalidraw/02-single-node.excalidraw) | Title and default `generic` node type |
| 3 | [`03-basic-relationship.json`](../examples/03-basic-relationship.json) | 2 | 1 | [`puml`](../examples/plantuml/03-basic-relationship.puml) | [`excalidraw`](../examples/excalidraw/03-basic-relationship.excalidraw) | Actor, service, direction, and labeled edge |
| 4 | [`04-database-flow.json`](../examples/04-database-flow.json) | 3 | 2 | [`puml`](../examples/plantuml/04-database-flow.puml) | [`excalidraw`](../examples/excalidraw/04-database-flow.excalidraw) | Three-stage request and database flow |
| 5 | [`05-queued-workflow.json`](../examples/05-queued-workflow.json) | 4 | 3 | [`puml`](../examples/plantuml/05-queued-workflow.puml) | [`excalidraw`](../examples/excalidraw/05-queued-workflow.excalidraw) | Queue and asynchronous worker |
| 6 | [`06-service-fan-out.json`](../examples/06-service-fan-out.json) | 5 | 5 | [`puml`](../examples/plantuml/06-service-fan-out.puml) | [`excalidraw`](../examples/excalidraw/06-service-fan-out.excalidraw) | Fan-out, merge, and all-purpose generic node |
| 7 | [`07-event-driven-ordering.json`](../examples/07-event-driven-ordering.json) | 6 | 6 | [`puml`](../examples/plantuml/07-event-driven-ordering.puml) | [`excalidraw`](../examples/excalidraw/07-event-driven-ordering.excalidraw) | Event-driven persistence and fulfillment |
| 8 | [`08-microservices-system.json`](../examples/08-microservices-system.json) | 9 | 10 | [`puml`](../examples/plantuml/08-microservices-system.puml) | [`excalidraw`](../examples/excalidraw/08-microservices-system.excalidraw) | Gateway fan-out and database-per-service |
| 9 | [`09-resilient-observability-loop.json`](../examples/09-resilient-observability-loop.json) | 11 | 15 | [`puml`](../examples/plantuml/09-resilient-observability-loop.puml) | [`excalidraw`](../examples/excalidraw/09-resilient-observability-loop.excalidraw) | Retry cycle, dead letters, metrics, alerts, and replay |
| 10 | [`10-commerce-platform.json`](../examples/10-commerce-platform.json) | 15 | 22 | [`puml`](../examples/plantuml/10-commerce-platform.puml) | [`excalidraw`](../examples/excalidraw/10-commerce-platform.excalidraw) | Multi-actor commerce platform with synchronous and event-driven paths |

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

Write the PlantUML result safely to a file:

```bash
diagrams-cli examples/04-database-flow.json -o database-flow.puml
```

Write the Excalidraw result safely to a file:

```bash
diagrams-cli examples/04-database-flow.json \
  --format excalidraw \
  -o database-flow.excalidraw
```

## Results by output format

| Sample | PlantUML path | Excalidraw path |
| --- | --- | --- |
| 01 — Empty diagram | Exit `0`; golden source | Exit `0`; golden JSON |
| 02 — Single node | Exit `0`; golden source | Exit `0`; golden JSON |
| 03 — Basic relationship | Exit `0`; golden source | Exit `0`; golden JSON |
| 04 — Database flow | Exit `0`; golden source | Exit `0`; golden JSON |
| 05 — Queued workflow | Exit `0`; golden source | Exit `0`; golden JSON |
| 06 — Service fan-out | Exit `0`; golden source | Exit `0`; golden JSON |
| 07 — Event-driven ordering | Exit `0`; golden source | Exit `0`; golden JSON |
| 08 — Microservices system | Exit `0`; golden source | Exit `0`; golden JSON |
| 09 — Resilient observability loop | Exit `0`; golden source | Exit `0`; golden JSON |
| 10 — Commerce platform | Exit `0`; golden source | Exit `0`; golden JSON |

## Recorded CLI output

The PlantUML run for `03-basic-relationship.json` now returns:

```plantuml
@startuml
title Client and API
left to right direction

actor "Web Client" as node_1
component "Public API" as node_2

node_1 --> node_2 : HTTPS request
@enduml
```

The Excalidraw run for the same input returns a version 2 Excalidraw document
containing a title, one bound arrow, two shapes, three text labels, and stable
metadata. Its complete result is checked in at
[`03-basic-relationship.excalidraw`](../examples/excalidraw/03-basic-relationship.excalidraw).

## Renderer fixture use

The sample inputs now serve as renderer fixtures:

- PlantUML runs are compared with byte-stable checked-in `.puml` text.
- All ten PlantUML golden files pass `plantuml -checkonly` syntax validation.
- Excalidraw runs are compared with byte-stable `.excalidraw` JSON and
  structurally checked for metadata, element arrays, and non-overlapping node
  placements.
