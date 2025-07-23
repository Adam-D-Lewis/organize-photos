# Organize Photos

A command-line tool to organize photos by date and detect duplicates.

## Features

- Organize JPEG images into a `YYYY/MM/DD` folder structure based on EXIF data.
- Detect duplicate images using SHA256 hashing.
- Generate a CSV report of duplicate files.
- Log errors without interrupting the process.
- Handle file name conflicts automatically.

## Installation

It is recommended to install this tool in a virtual environment.

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package in editable mode
pip install -e .
```

## Usage

```bash
# Move files
organize-photos --source /path/to/first/album --destination /path/to/organized-photos

# Copy files
organize-photos --source /path/to/first/album --destination /path/to/organized-photos --copy
  ```
 
+### Deleting Duplicates
+
+After running the `organize` command, you can delete duplicate files using the generated `duplicates.csv` report.
+
+```bash
+# Run the dedupe command with the report
+organize-photos dedupe --report /path/to/organized-photos/duplicates.csv
+
+# Skip the confirmation prompt
+organize-photos dedupe --report /path/to/organized-photos/duplicates.csv --yes
+```

## Dependencies

- [Click](https://click.palletsprojects.com/)
- [tqdm](https://github.com/tqdm/tqdm)
- [Pillow](https://python-pillow.org/)

## Development

To set up the development environment, including all test dependencies, run the following command in your virtual environment:

```bash
pip install -e .[dev]
```

### Running Tests

To run the test suite, use `pytest`:

```bash
pytest
```