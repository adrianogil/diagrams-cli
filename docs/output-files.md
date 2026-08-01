# Output files and overwrite protection

## Status

`diagrams-cli` can write generated PlantUML source directly to a file with
`--output/-o`. Standard output remains the default when no output path is
given.

```text
Diagram -> renderer -> stdout
                    `-> validated output path -> protected UTF-8 file
```

Excalidraw output paths are validated, but file creation is refused until the
Excalidraw renderer is implemented. The CLI never writes placeholder text into
an `.excalidraw` document.

## Basic usage

Write PlantUML to stdout:

```bash
diagrams-cli examples/04-database-flow.json
```

Create a PlantUML file:

```bash
diagrams-cli examples/04-database-flow.json \
  --output database-flow.puml
```

The short option is equivalent:

```bash
diagrams-cli examples/04-database-flow.json -o database-flow.puml
```

Successful file output writes nothing to stdout.

## Extension rules

| Format | Required extension |
| --- | --- |
| `plantuml` | `.puml` |
| `excalidraw` | `.excalidraw` |

Extension comparisons are case-insensitive. A path without the expected
extension is rejected before rendering or writing:

```text
diagrams-cli: error: plantuml output path must use the .puml extension: diagram.txt
```

`--output -` is not supported yet. Omitting `--output` is the current way to
write to stdout.

## Overwrite protection

Existing files are preserved by default:

```bash
diagrams-cli architecture.json -o architecture.puml
```

If `architecture.puml` already exists, the command exits with an error:

```text
diagrams-cli: error: output file already exists; use --force to overwrite: architecture.puml
```

Allow replacement explicitly:

```bash
diagrams-cli architecture.json -o architecture.puml --force
```

For non-forced writes, the implementation uses exclusive file creation rather
than only checking existence first. This prevents another process from
creating the destination between the check and the write.

`--force` without `--output` is an argument error because there is no file to
replace.

## Filesystem behavior

- Files are written as UTF-8 text with newline-preserving output.
- Parent directories are not created automatically.
- A missing parent directory produces a concise error.
- A directory cannot be used as an output file.
- Other operating-system write failures are reported without a traceback.
- Output failures return exit code `1`.
- Invalid CLI combinations such as `--force` without `--output` use
  `argparse`'s exit code `2`.

## Excalidraw boundary

This command validates the `.excalidraw` extension but returns an error and
does not create a file:

```bash
diagrams-cli architecture.json \
  --format excalidraw \
  --output architecture.excalidraw
```

File writing will become available automatically once the Excalidraw renderer
replaces its current placeholder path.

## Python API

Validate a destination without writing:

```python
from diagrams_cli.output import validate_output_path

destination = validate_output_path("architecture.puml", "plantuml")
```

Write generated content safely:

```python
from diagrams_cli.output import write_output_file

write_output_file(
    plantuml_source,
    "architecture.puml",
    "plantuml",
    force=False,
)
```

Both functions raise `DiagramOutputError` for expected output failures.

## Verification coverage

Unit and CLI integration tests cover:

- Long and short output options
- Default stdout behavior
- PlantUML file creation without stdout noise
- Case-insensitive format extensions
- Invalid PlantUML and Excalidraw extensions
- Preservation of existing files
- Explicit forced replacement
- Missing parent directories and directory destinations
- `--force` without `--output`
- Refusal to create placeholder Excalidraw files

## Remaining output roadmap

- Support `-` as an explicit stdin/stdout path.
- Make the positional input behavior consistent with future stdin support.
- Finish standardizing exit-code and stderr conventions.
- Enable `.excalidraw` file writing after its renderer exists.
