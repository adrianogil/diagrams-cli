# diagrams-cli

Generate PlantUML and Excalidraw diagrams from a shared JSON description.

## Status

The renderer-independent diagram model, UTF-8 JSON loader, schema validation,
and CLI validation path are implemented. Output generation is still an
explicit placeholder.

See the detailed documentation:

- [Architecture and input schema](docs/architecture-and-input-schema.md)
- [Implementation plan](docs/implementation-plan.md)
- [Ten progressively complex samples](docs/samples.md)

## Development checks

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```
