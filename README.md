# diagrams-cli

Generate PlantUML and Excalidraw diagrams from a shared JSON description.

## Status

The renderer-independent diagram model, UTF-8 JSON loader, schema validation,
and deterministic PlantUML generation to stdout are implemented. Excalidraw
generation remains an explicit placeholder. PlantUML can also be written to a
protected `.puml` output file.

See the detailed documentation:

- [Architecture and input schema](docs/architecture-and-input-schema.md)
- [PlantUML renderer](docs/plantuml-renderer.md)
- [Output files and overwrite protection](docs/output-files.md)
- [Implementation plan](docs/implementation-plan.md)
- [Ten progressively complex samples](docs/samples.md)

Generate PlantUML from an example:

```bash
diagrams-cli examples/04-database-flow.json --format plantuml
diagrams-cli examples/04-database-flow.json -o database-flow.puml
```

## Development checks

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```
