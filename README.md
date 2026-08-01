# diagrams-cli

Generate PlantUML and Excalidraw diagrams from a shared JSON description.

## Status

The renderer-independent diagram model, UTF-8 JSON loader, schema validation,
and deterministic PlantUML and Excalidraw renderers are implemented. Both
formats support stdout and protected output files.

See the detailed documentation:

- [Architecture and input schema](docs/architecture-and-input-schema.md)
- [PlantUML renderer](docs/plantuml-renderer.md)
- [Excalidraw renderer and layout](docs/excalidraw-renderer.md)
- [Output files and overwrite protection](docs/output-files.md)
- [Implementation plan](docs/implementation-plan.md)
- [Ten progressively complex samples](docs/samples.md)
- [Testing, golden fixtures, and installed CLI coverage](docs/testing.md)

## Installation

Install from a local checkout:

```bash
python -m pip install .
```

This provides both supported command forms:

```bash
diagrams-cli --version
python -m diagrams_cli --version
```

Generate PlantUML from an example:

```bash
diagrams-cli examples/04-database-flow.json --format plantuml
diagrams-cli examples/04-database-flow.json -o database-flow.puml
```

Generate an editable Excalidraw document:

```bash
diagrams-cli examples/04-database-flow.json \
  --format excalidraw \
  -o database-flow.excalidraw
```

Both commands are exercised from an isolated wheel installation by the
end-to-end test suite.

## Development checks

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```
