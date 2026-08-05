# Architecture and input schema

## Current status

`diagrams-cli` implements the validated input pipeline and three renderers:

```text
UTF-8 JSON file -> JSON decoding -> schema validation -> diagram model
                                                        |-> PlantUML stdout
                                                        |-> Mermaid flowchart
                                                        `-> layered layout
                                                             `-> Excalidraw JSON
```

## Package responsibilities

- `diagrams_cli.model` defines the immutable, renderer-independent domain
  model: `Diagram`, `Node`, and `Edge`.
- `diagrams_cli.validation` validates decoded JSON values and converts them
  into the domain model.
- `diagrams_cli.loader` reads UTF-8 JSON files or JSON strings and delegates
  schema validation.
- `diagrams_cli.errors` provides the expected input-error hierarchy.
- `diagrams_cli.renderers` defines the common callable renderer interface.
- `diagrams_cli.renderers.plantuml` produces deterministic PlantUML source.
- `diagrams_cli.renderers.mermaid` produces deterministic Mermaid flowchart
  text.
- `diagrams_cli.layout` assigns deterministic, non-overlapping node positions
  by graph depth, direction, and input order.
- `diagrams_cli.renderers.excalidraw` produces deterministic editable
  Excalidraw JSON with shapes, labels, and bound arrows.
- `diagrams_cli.output` validates format extensions and writes output without
  implicit overwrites.
- `diagrams_cli.cli` handles CLI arguments and reports loading or validation
failures without a traceback and selects any renderer for stdout or
protected file output.

Keeping the input model independent from output formats allows all three
renderers to consume the same validated diagram.

## JSON document

A document is a JSON object with these fields:

| Field | Required | Type | Default |
| --- | --- | --- | --- |
| `title` | No | Non-empty string | `null` |
| `direction` | No | `top-to-bottom` or `left-to-right` | `top-to-bottom` |
| `nodes` | Yes | Array of node objects | None |
| `edges` | No | Array of edge objects | Empty array |

Unknown fields are rejected so spelling mistakes do not silently change a
diagram.

### Nodes

Each node supports:

| Field | Required | Type | Default |
| --- | --- | --- | --- |
| `id` | Yes | Non-empty string, unique in the document | None |
| `label` | Yes | Non-empty string | None |
| `type` | No | Supported node type | `generic` |

Supported node types are `actor`, `service`, `database`, `queue`, and
`generic`.

### Edges

Each directed edge supports:

| Field | Required | Type | Default |
| --- | --- | --- | --- |
| `from` | Yes | ID of an existing node | None |
| `to` | Yes | ID of an existing node | None |
| `label` | No | String | `null` |

Both endpoints must reference nodes declared in the same document. Self-edges
and multiple edges between the same pair of nodes are currently allowed.

## Complete example

```json
{
  "title": "Order Processing",
  "direction": "left-to-right",
  "nodes": [
    {
      "id": "client",
      "label": "Web Client",
      "type": "actor"
    },
    {
      "id": "api",
      "label": "Orders API",
      "type": "service"
    },
    {
      "id": "orders-db",
      "label": "Orders DB",
      "type": "database"
    }
  ],
  "edges": [
    {
      "from": "client",
      "to": "api",
      "label": "POST /orders"
    },
    {
      "from": "api",
      "to": "orders-db",
      "label": "Store order"
    }
  ]
}
```

## Python API

Load and validate a file:

```python
from diagrams_cli.loader import load_diagram

diagram = load_diagram("architecture.json")
```

Load and validate an in-memory JSON string:

```python
from diagrams_cli.loader import loads_diagram

diagram = loads_diagram('{"nodes": []}')
```

Validate an already decoded JSON-compatible value:

```python
from diagrams_cli.validation import parse_diagram

diagram = parse_diagram({"nodes": []})
```

The returned data classes are frozen and use tuples for node and edge
collections. Renderers can therefore consume them without mutating validated
input state.

## Errors

Expected failures inherit from `DiagramError`:

- `DiagramLoadError` covers missing/unreadable files, non-UTF-8 input, and
  malformed JSON. JSON syntax errors include their source, line, and column.
- `DiagramValidationError` covers schema errors. Messages use paths such as
  `document.nodes[1].id` and `document.edges[0].to`.

For example:

```text
diagrams-cli: error: document.edges[1].to references unknown node "payments-db"
```

The CLI returns `1` for JSON loading or schema-validation failures. Existing
argument and path checks retain their current CLI behavior.

## Current limitations

- Input is file-only at the CLI layer; `loads_diagram` already supports the
  future stdin path.
- PlantUML source is written to stdout; image rendering is not invoked.
- Mermaid source is generated without invoking the Mermaid CLI or a browser.
- Styling, groups, node coordinates, and renderer-specific options are not
  part of the initial portable schema.
- Excalidraw layout does not route arrows or labels around unrelated elements.

Thirty inputs and golden results from both CLI format paths are available in
[Sample diagrams](samples.md). The original ten form a complexity progression;
twenty focused scenarios add self-loops, disconnected graphs, cycles, joins,
feedback paths, and varied application domains. Layout and output details are
covered in [Excalidraw renderer](excalidraw-renderer.md).
