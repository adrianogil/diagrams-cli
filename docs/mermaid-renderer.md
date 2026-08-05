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

## Determinism and safety

Nodes receive aliases such as `node_1` in input order, so user-controlled IDs
never become Mermaid identifiers. Labels escape quotes, angle brackets,
vertical bars, backticks, ampersands, and line breaks before entering quoted
Mermaid strings. Repeated rendering of the same validated model is
byte-identical and ends with one newline.

The backend emits Mermaid source only. Rendering SVG or PNG remains the
responsibility of Mermaid-compatible tools and Markdown viewers.
