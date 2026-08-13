# Implementation plan

## Goal

Turn `diagrams-cli` into a deterministic converter from one validated JSON
diagram format to PlantUML, Excalidraw, and Mermaid outputs.

The intended pipeline is:

```text
input -> decode -> validate -> diagram model -> optional layout -> renderer -> output
```

## Phase 1: Input model and validation — complete

- [x] Define immutable `Diagram`, `Node`, `Edge`, `Group`, and `Swimlane` data
      classes.
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
- [x] Add twenty focused scenarios covering additional graph structures.
- [x] Record CLI results for all supported format selections.

Acceptance result: valid JSON reaches renderer selection; invalid JSON or
schema input produces a concise error without a traceback. Thirty-one distinct
examples now cover progressive complexity plus self-loops, disconnected
graphs, cycles, joins, feedback paths, and varied architecture domains.

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

Acceptance result: all thirty-one example inputs produce byte-stable golden PlantUML
files, the CLI writes generated source to stdout, unsafe source IDs never
become aliases, and every golden file passes local PlantUML syntax checking.

## Phase 3: Output handling and CLI conventions — in progress

- [x] Add `--output/-o` with stdout as the default.
- [ ] Support `-` for stdin and stdout.
- [x] Validate `.puml`, `.excalidraw`, and `.mmd` extensions when a path is
      supplied.
- [x] Refuse to overwrite existing files unless `--force` is present.
- [x] Report filesystem errors without tracebacks.
- [ ] Make the positional input argument required through `argparse` or
      document the stdin exception clearly.
- [ ] Standardize exit codes and stderr behavior.
- [x] Add temporary-directory CLI integration tests.

Acceptance criteria:

- Pipes and files both work predictably.
- Existing user files are never overwritten implicitly.
- Help text documents defaults and output rules.

Progress result: all three renderers support stdout and protected format-specific
files, extensions are format-aware, exclusive creation prevents overwrite
races, and `--force` explicitly enables replacement. Explicit `-` streams and
broader CLI convention cleanup remain open.

## Phase 4: Excalidraw layout and renderer — complete

- [x] Define a deterministic layered-layout result model.
- [x] Place nodes by graph depth for both supported directions.
- [x] Handle disconnected nodes and graph cycles predictably.
- [x] Render node shapes, labels, and bound arrows.
- [x] Map portable node types to a small visual vocabulary.
- [x] Emit required Excalidraw document metadata.
- [x] Derive stable element IDs without timestamps or randomness.
- [x] Add golden `.excalidraw` fixtures and structural assertions.
- [x] Replace the Excalidraw placeholder path with generated JSON.

Acceptance criteria:

- Generated files open in Excalidraw.
- Nodes do not overlap in the supported fixture set.
- Repeated runs produce reviewable, deterministic output.

Acceptance result: all thirty-one examples produce byte-stable Excalidraw version 2
documents with non-overlapping node placements, stable metadata, bound arrows,
and editable text. Strongly connected components make cycles finite and
predictable, disconnected nodes retain input order, and the CLI supports both
stdout and protected `.excalidraw` files.

## Phase 5: Mermaid renderer — complete

- [x] Map portable directions and node types to Mermaid flowchart syntax.
- [x] Render diagram titles and labeled directed edges.
- [x] Isolate user IDs behind deterministic aliases.
- [x] Escape label content that could alter Mermaid syntax.
- [x] Add `--format mermaid` and protected `.mmd` output.
- [x] Add renderer, CLI, output, and installed-command tests.
- [x] Document Mermaid usage, mappings, determinism, and limitations.

Acceptance result: validated JSON produces deterministic Mermaid flowchart
text on stdout or in protected `.mmd` files. Every portable node type and both
directions are supported, unsafe IDs are never emitted, and labels cannot add
unintended Mermaid statements.

## Phase 6: Portable groups and swimlanes — complete

- [x] Extend the immutable model and strict JSON schema with groups and
      swimlanes.
- [x] Define unique boundary IDs, node-only membership, and non-empty member
      lists.
- [x] Reject duplicate or dangling members and multiple memberships of the
      same boundary type.
- [x] Permit one group plus one swimlane per node only when the entire group
      shares one lane; reject recursive, partial, or cross-lane nesting.
- [x] Preserve declaration and member order deterministically.
- [x] Render PlantUML packages inside swimlane frames.
- [x] Render Mermaid nested subgraphs with direction and safe aliases.
- [x] Add boundary-aware Excalidraw bands, containers, padding, and
      non-overlapping layout.
- [x] Preserve the existing renderer paths and golden bytes for documents
      without groups or swimlanes.
- [x] Add schema, layout, renderer, escaping, invalid-input, CLI, installed
      wheel, and representative golden coverage.
- [x] Document the compatibility and boundary contract across all outputs.

Acceptance result: one portable membership model produces useful architectural
boundaries in PlantUML, Mermaid, and Excalidraw. The thirty-first example
exercises nested groups in two swimlanes, and all prior goldens remain
byte-identical.

## Phase 7: Packaging, automation, and documentation

- [x] Add installed-command tests for `diagrams-cli` and
      `python -m diagrams_cli`.
- [x] Compare both installed entry points with renderer golden fixtures.
- [ ] Add CI across supported Python versions.
- [ ] Add linting, formatting, type checking, and coverage configuration.
- [ ] Build and inspect wheel and source distributions.
- [ ] Use one source of truth for the package version.
- [x] Complete README installation and end-to-end examples.
- [ ] Add troubleshooting and exit-code references.
- [x] Document schema compatibility and future evolution rules.

Acceptance criteria:

- CI verifies tests, compilation, builds, and installed entry points.
- A new user can install the package and generate all three formats from the
  documented example.

Progress result: the test suite builds a wheel without network-dependent build
isolation, installs it into a temporary virtual environment, removes source
checkout import paths, and exercises both installed entry points as
subprocesses. All thirty-one PlantUML and all thirty-one Excalidraw stdout
results plus the representative boundary Mermaid result are checked
byte-for-byte. File output, overwrite protection, help, version, invalid JSON,
and extension errors are covered. CI, static-analysis configuration,
source-distribution inspection, centralized versioning, and troubleshooting
documentation remain open.

## Deferred extensions

These should be considered only after the core renderers are stable:

- Explicit positioning hints
- Styles and themes
- Additional edge types
- JSON Schema publication
- Additional output formats beyond PlantUML, Excalidraw, and Mermaid
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
