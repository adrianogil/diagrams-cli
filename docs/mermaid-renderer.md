# Mermaid renderer

## Usage

Generate Mermaid flowchart text on stdout:

```bash
diagrams-cli examples/04-database-flow.json --format mermaid
```

Write a protected `.mmd` file:

```bash
diagrams-cli examples/04-database-flow.json \
  --format mermaid \
  --output database-flow.mmd
```

Existing output files require `--force`, following the same overwrite rules as
the other renderers.

## Portable mappings

The renderer emits `flowchart TD` for `top-to-bottom` diagrams and
`flowchart LR` for `left-to-right` diagrams. Portable node types map to these
Mermaid shapes:

| Node type | Mermaid shape |
| --- | --- |
| `actor` | Stadium |
| `service` | Rectangle |
| `database` | Cylinder |
| `queue` | Subroutine |
| `generic` | Rectangle |

Edges use directed arrows and retain optional labels. A diagram title is
written through Mermaid YAML frontmatter.

## Groups and swimlanes

Both portable boundary types render as named Mermaid `subgraph` blocks.
Swimlane blocks use aliases such as `swimlane_1`; group blocks use aliases such
as `group_1`. A group shared by one lane is nested inside that lane. Each block
repeats the diagram's `TD` or `LR` direction so its members follow the same
reading direction as the overall flowchart.

Validated member order determines where a nested group is encountered. Nodes
are declared once, while edges remain outside subgraphs so relationships can
cross any boundary. Boundary labels use the same escaping as node and edge
labels, and source boundary IDs never become Mermaid identifiers.

## Determinism and safety

Nodes receive aliases such as `node_1` in input order, so user-controlled IDs
never become Mermaid identifiers. Labels escape quotes, angle brackets,
vertical bars, backticks, ampersands, and line breaks before entering quoted
Mermaid strings. Repeated rendering of the same validated model is
byte-identical and ends with one newline.

The backend emits Mermaid source only. Rendering SVG or PNG remains the
responsibility of Mermaid-compatible tools and Markdown viewers.

The boundary example has a checked-in representative Mermaid golden at
`examples/mermaid/31-platform-boundaries.mmd`.
