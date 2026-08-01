# Testing and golden fixtures

## Test strategy

The test suite has three boundaries:

```text
unit tests -> in-process CLI tests -> built-and-installed subprocess tests
```

- Unit tests cover validation, layout, renderers, and output helpers directly.
- In-process CLI tests call `diagrams_cli.cli.main` with controlled streams and
  temporary files for focused argument and error assertions.
- End-to-end tests build a wheel, install it into a temporary virtual
  environment, and launch the installed entry points as subprocesses.

The layers intentionally overlap on critical behavior. A renderer unit test
can identify a formatting regression precisely, while an installed-command
test catches missing packages, broken entry-point metadata, encoding problems,
or differences at the process boundary.

## Golden fixture inventory

The same thirty JSON inputs drive both renderer fixture sets:

```text
examples/*.json
examples/plantuml/*.puml
examples/excalidraw/*.excalidraw
```

There are thirty PlantUML and thirty Excalidraw golden files. The original ten
inputs increase progressively in size; the next twenty target distinct graph
structures and application domains. A golden is the exact UTF-8 output
expected for its input, including whitespace and the final newline. This makes
determinism regressions visible in code review.

`tests/test_examples.py` verifies the renderers directly. It also checks the
Excalidraw document structure and confirms that node rectangles do not overlap
in any supported sample.

## Installed-command end-to-end tests

`tests/test_cli_e2e.py` performs this setup once for its test class:

1. Build a wheel from the repository without downloading dependencies.
2. Create a temporary virtual environment.
3. Install the wheel without dependencies.
4. Remove `PYTHONPATH` and disable user-site packages for subprocesses.
5. Run commands outside the source tree so imports must come from the wheel.

The subprocess coverage verifies:

| Boundary | Coverage |
| --- | --- |
| Installed `diagrams-cli` | All thirty PlantUML stdout goldens |
| Installed `python -m diagrams_cli` | All thirty Excalidraw stdout goldens |
| Both installed entry points | Help, version, and format-specific file output |
| Installed console script | Existing-file refusal and explicit `--force` replacement |
| Installed module | Invalid JSON and invalid output-extension failures |

Successful commands must return `0`, match their golden bytes, and keep stderr
empty. Expected input or output failures must return the documented nonzero
code and must not expose a traceback.

## Running tests

Run everything, including the isolated wheel installation and subprocesses:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Run only the fast in-process tests:

```bash
PYTHONPATH=src python -m unittest \
  tests.test_cli \
  tests.test_examples \
  tests.test_excalidraw \
  tests.test_layout \
  tests.test_loader \
  tests.test_output \
  tests.test_plantuml \
  -v
```

Run only the installed-command boundary:

```bash
PYTHONPATH=src python -m unittest tests.test_cli_e2e -v
```

Compile the source and tests after changing Python files:

```bash
python -m compileall -q src tests
```

## Updating goldens

Golden changes must be intentional. First change the renderer, then regenerate
the affected artifact with the CLI and inspect the diff:

```bash
PYTHONPATH=src python -m diagrams_cli \
  examples/04-database-flow.json \
  --format plantuml \
  --output examples/plantuml/04-database-flow.puml \
  --force
```

```bash
PYTHONPATH=src python -m diagrams_cli \
  examples/04-database-flow.json \
  --format excalidraw \
  --output examples/excalidraw/04-database-flow.excalidraw \
  --force
```

Run the complete suite after regeneration. Never update a golden only to make
a failing test pass without understanding the output change.

## Environment requirements

The installed-command tests require Python's `venv` module and `pip`. Wheel
build requirements must already be available locally because the build uses
`--no-build-isolation`; the test does not rely on network access. All temporary
wheel, environment, output, and malformed-input files are removed after the
test class completes.
