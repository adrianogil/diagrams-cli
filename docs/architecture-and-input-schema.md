# Architecture and input schema

## Current status

`diagrams-cli` currently implements the input half of the generation
pipeline:

```text
UTF-8 JSON file -> JSON decoding -> schema validation -> diagram model
```

The CLI performs this pipeline before printing its explicit placeholder
message. PlantUML and Excalidraw renderers are planned but are not yet
implemented.

## Package responsibilities

- `diagrams_cli.model` defines the immutable, renderer-independent domain
  model: `Diagram`, `Node`, and `Edge`.
- `diagrams_cli.validation` validates decoded JSON values and converts them
  into the domain model.
- `diagrams_cli.loader` reads UTF-8 JSON files or JSON strings and delegates
  schema validation.
- `diagrams_cli.errors` provides the expected input-error hierarchy.
- `diagrams_cli.cli` handles CLI arguments and reports loading or validation
  failures without a traceback.

Keeping the input model independent from output formats allows PlantUML and
Excalidraw renderers to consume the same validated diagram.

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

- No PlantUML or Excalidraw content is generated yet.
- No output-file option exists yet.
- Input is file-only at the CLI layer; `loads_diagram` already supports the
  future stdin path.
- Styling, groups, node coordinates, and renderer-specific options are not
  part of the initial portable schema.

Ten progressively complex inputs and the recorded results from both CLI format
paths are available in [Sample diagrams](samples.md).
