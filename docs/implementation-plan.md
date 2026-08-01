# Implementation plan

## Goal

Turn `diagrams-cli` into a deterministic converter from one validated JSON
diagram format to PlantUML and Excalidraw outputs.

The intended pipeline is:

```text
input -> decode -> validate -> diagram model -> optional layout -> renderer -> output
```

## Phase 1: Input model and validation — complete

- [x] Define immutable `Diagram`, `Node`, and `Edge` data classes.
- [x] Define portable directions and node types.
- [x] Load UTF-8 JSON from files and strings.
- [x] Report JSON source, line, and column on decoding failures.
- [x] Validate document, node, and edge shapes.
- [x] Reject duplicate node IDs and dangling edge endpoints.
- [x] Reject unknown fields and unsupported enum values.
- [x] Integrate loading and validation into the current CLI.
- [x] Add unit and CLI tests for successful and failing inputs.
- [x] Document the schema, API, errors, and current limitations.
- [x] Add ten progressively complex validated examples.
- [x] Record CLI results for both format selections.

Acceptance result: valid JSON reaches renderer selection; invalid JSON or
schema input produces a concise error without a traceback.

## Phase 2: PlantUML renderer — complete

- [x] Add a renderer protocol or common renderer interface.
- [x] Map portable node types to PlantUML constructs.
- [x] Render title and direction.
- [x] Render directed, optionally labeled edges.
- [x] Escape labels and identifiers safely.
- [x] Keep output order deterministic.
- [x] Add unit tests and golden `.puml` fixtures.
- [x] Replace the PlantUML placeholder path with generated text.

Acceptance criteria:

- A documented example produces syntactically valid PlantUML.
- Labels cannot inject unintended PlantUML statements.
- Repeated runs with the same input produce byte-identical output.

Acceptance result: all ten example inputs produce byte-stable golden PlantUML
files, the CLI writes generated source to stdout, unsafe source IDs never
become aliases, and every golden file passes local PlantUML syntax checking.

## Phase 3: Output handling and CLI conventions

- [ ] Add `--output/-o` with stdout as the default.
- [ ] Support `-` for stdin and stdout.
- [ ] Validate `.puml` and `.excalidraw` extensions when a path is supplied.
- [ ] Refuse to overwrite existing files unless `--force` is present.
- [ ] Report filesystem errors without tracebacks.
- [ ] Make the positional input argument required through `argparse` or
      document the stdin exception clearly.
- [ ] Standardize exit codes and stderr behavior.
- [ ] Add temporary-directory CLI integration tests.

Acceptance criteria:

- Pipes and files both work predictably.
- Existing user files are never overwritten implicitly.
- Help text documents defaults and output rules.

## Phase 4: Excalidraw layout and renderer

- [ ] Define a deterministic layered-layout result model.
- [ ] Place nodes by graph depth for both supported directions.
- [ ] Handle disconnected nodes and graph cycles predictably.
- [ ] Render node shapes, labels, and bound arrows.
- [ ] Map portable node types to a small visual vocabulary.
- [ ] Emit required Excalidraw document metadata.
- [ ] Derive stable element IDs without timestamps or randomness.
- [ ] Add golden `.excalidraw` fixtures and structural assertions.
- [ ] Replace the Excalidraw placeholder path with generated JSON.

Acceptance criteria:

- Generated files open in Excalidraw.
- Nodes do not overlap in the supported fixture set.
- Repeated runs produce reviewable, deterministic output.

## Phase 5: Packaging, automation, and documentation

- [ ] Add installed-command tests for `diagrams-cli` and
      `python -m diagrams_cli`.
- [ ] Add CI across supported Python versions.
- [ ] Add linting, formatting, type checking, and coverage configuration.
- [ ] Build and inspect wheel and source distributions.
- [ ] Use one source of truth for the package version.
- [ ] Complete README installation and end-to-end examples.
- [ ] Add troubleshooting and exit-code references.
- [ ] Document schema compatibility and future evolution rules.

Acceptance criteria:

- CI verifies tests, compilation, builds, and installed entry points.
- A new user can install the package and generate both formats from the
  documented example.

## Deferred extensions

These should be considered only after both core renderers are stable:

- Groups or containers
- Explicit positioning hints
- Styles and themes
- Additional edge types
- JSON Schema publication
- Additional output formats
- Watch mode or batch conversion

Portable concepts should remain in the common model. Renderer-specific
features should be isolated so one backend does not define the entire input
format.

## Work tracking

The ongoing project and task notes live in the Dev notes repository:

- `MainDevNotes/DevProjects/DiagramsCLI/diagrams-cli.md`
- `MainDevNotes/DevProjects/DiagramsCLI/Task - Implement diagrams-cli JSON-to-diagram pipeline.md`

Every implementation session should append a dated work-log entry to the task
note, update relevant subtasks, and record validation commands and commits.
