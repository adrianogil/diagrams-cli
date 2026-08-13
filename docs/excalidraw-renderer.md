# Excalidraw renderer

## Status

Excalidraw generation is implemented. Validated diagrams pass through a
deterministic layered layout and become editable Excalidraw JSON:

```text
UTF-8 JSON -> validation -> Diagram -> layered layout -> Excalidraw renderer
                                                          |-> stdout
                                                          `-> .excalidraw file
```

No browser, Excalidraw installation, or rendering service is required to
generate the document.

## CLI usage

Print Excalidraw JSON to the terminal:

```bash
diagrams-cli examples/04-database-flow.json --format excalidraw
```

Create an editable `.excalidraw` file:

```bash
diagrams-cli examples/04-database-flow.json \
  --format excalidraw \
  --output database-flow.excalidraw
```

Existing files are preserved unless `--force` is supplied. See
[Output files and overwrite protection](output-files.md) for the shared file
contract.

## Python API

```python
from diagrams_cli.loader import load_diagram
from diagrams_cli.renderers import render_excalidraw

diagram = load_diagram("examples/04-database-flow.json")
document_json = render_excalidraw(diagram)
```

`render_excalidraw` follows the common renderer signature:

```python
Renderer = Callable[[Diagram], str]
```

The layout can also be inspected separately:

```python
from diagrams_cli.layout import layout_diagram

layout = layout_diagram(diagram)
for placement in layout.placements:
    print(placement.node.id, placement.layer, placement.x, placement.y)
```

## Deterministic layered layout

For documents without boundaries, the layout derives graph depth before
rendering:

1. Calculate strongly connected components in node input order.
2. Collapse each component into one vertex, producing an acyclic graph.
3. Assign each component the maximum predecessor depth plus one.
4. Place nodes within each layer in input order.
5. Center smaller layers against the widest layer.

For `left-to-right`, graph depth changes the x-coordinate. For
`top-to-bottom`, depth changes the y-coordinate. Disconnected source nodes
start in layer zero. Nodes in a cycle share a layer, so layout always
terminates and remains stable. Fixed node sizes and gaps prevent node overlap.

Self-edges use a visible loop on the right side of their node. Other arrows
connect the facing horizontal or vertical boundaries of their endpoints.

Boundary documents use a deterministic container layout. Left-to-right
swimlanes become equal-width horizontal bands; top-to-bottom swimlanes become
equal-height vertical columns. Members follow declared lane order, groups are
placed at their first member, and group members follow group order. Fixed
header space, padding, and gaps keep labels readable, nodes non-overlapping,
groups inside their lane, and sibling groups or lanes separate. Graph-depth
layers are still calculated and retained in the layout result even though
container membership controls boundary-document coordinates.

## Visual vocabulary

| Portable type | Shape | Fill color |
| --- | --- | --- |
| `actor` | Ellipse | Light blue |
| `service` | Rounded rectangle | Light indigo |
| `database` | Ellipse | Light green |
| `queue` | Diamond | Light yellow |
| `generic` | Rounded rectangle | Light gray |

Each node consists of a shape and centered bound text element. Directed edges
are arrow elements bound to their source and target shapes. Edge labels are
independent text elements placed near the arrow midpoint.

Swimlanes are light-gray solid rounded rectangles. Groups are light-indigo
dashed rounded rectangles. Boundary elements are emitted before arrows and
nodes so they behave as visual backgrounds, with independent editable labels
in their header space.

## Excalidraw document structure

The emitted root object contains:

- `type: "excalidraw"`
- Excalidraw document `version: 2`
- `source: "diagrams-cli"`
- Ordered `elements`
- Minimal `appState` with a white canvas and no grid
- Empty `files`, because the portable model has no binary assets

Elements include the base shape fields used by Excalidraw restoration,
including geometry, colors, stroke settings, version data, bindings, and
locking/deletion state. Text and arrow elements add their type-specific
fields.

The structure follows Excalidraw's own `serializeAsJSON` root contract and
restoration defaults:

- [Official JSON serializer](https://github.com/excalidraw/excalidraw/blob/master/packages/excalidraw/data/json.ts)
- [Official element restoration](https://github.com/excalidraw/excalidraw/blob/master/packages/excalidraw/data/restore.ts)

## Determinism

The same validated model produces byte-identical output:

- Elements retain stable diagram order.
- Shape, label, title, and edge IDs use sequential semantic names.
- Seeds and version nonces come from SHA-256 of each stable element ID.
- Element versions and update values are fixed initial values.
- Layout uses no random choices, timestamps, font measurements, or external
  services.
- JSON uses stable insertion order, two-space indentation, UTF-8 characters,
  and one final newline.

Every JSON sample has a checked-in golden file under `examples/excalidraw/`.

## Verification

The automated suite checks:

- Required document metadata
- Every node type's shape and color
- Title, node text, and edge text
- Container and arrow bindings
- Both layout directions
- Disconnected graphs, multi-node cycles, and self-edges
- Groups nested in swimlanes, standalone groups, both lane orientations, and
  containment/non-overlap invariants
- Stable IDs, seeds, version values, and timestamps
- No node overlap across all thirty-one examples
- CLI stdout and protected file output
- Byte-for-byte golden output for all thirty-one examples

Run the checks:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```

## Current limitations

- Layout does not route arrows around unrelated nodes.
- Edge labels are placed near arrow midpoints but do not participate in
  collision avoidance.
- Actor and database nodes use distinct colors but share the ellipse shape.
- Explicit positioning, themes, recursive boundary nesting, and images are
  outside the portable schema.
- The CLI still accepts input files only; stdin and explicit `-` streams remain
  planned.
