# CLI Developer Guide

## Overview
This guide provides instructions for developers working on the LPP-Detect CLI module.

## Project Structure
The CLI module is located in `vigia_detect/cli/`.
- `process_images.py`: Main CLI script.
- `tests/`: Unit tests for the CLI.

## Dependencies
The CLI depends on other modules within the `vigia_detect` project:
- `cv_pipeline`: For image processing and detection.
- `db`: For Supabase integration.
- `utils`: For image utility functions.

Ensure these modules are correctly imported and initialized. The `sys.path.append` in `process_images.py` handles the root directory import.

## Adding New Features
1.  **Identify the requirement:** Clearly define the new feature or modification needed.
2.  **Locate relevant code:** Determine which functions or classes in `process_images.py` or its dependencies need changes.
3.  **Implement the logic:** Write the necessary Python code to add the feature. Adhere to existing coding standards and include type hints.
4.  **Update argument parsing:** If the feature requires new command-line arguments, modify the `parse_args()` function using `argparse`.
5.  **Integrate with `main()` or `process_directory()`:** Connect the new logic into the main execution flow.
6.  **Write tests:** Create or update tests in `vigia_detect/cli/tests/test_cli.py` to cover the new functionality.
7.  **Update documentation:**
    *   Modify `vigia_detect_docs/cli/README.md` to reflect changes in usage or features.
    *   Update `vigia_detect_docs/cli/api_reference.md` with any new functions, parameters, or data structures.
    *   Consider if changes are needed in the main `info.md` or sprint documentation.

## Testing
Run tests for the CLI module using `pytest`:
```bash
pytest vigia_detect/cli/tests/
```
Or use the project's test runner:
```bash
python run_tests.py
```
Ensure all tests pass before submitting changes.

## Error Handling
- Use Python's `logging` module for informative messages (info, warning, error).
- Implement `try...except` blocks for potentially failing operations (e.g., file processing, database calls).
- Aim for graceful degradation where possible (e.g., skip a single image if processing fails, but continue with others).

## Configuration
- Supabase connection relies on environment variables (`SUPABASE_URL`, `SUPABASE_KEY`). Ensure these are set in a `.env` file or the environment.
- Model type and confidence threshold are configurable via command-line arguments.

## Code Style
- Follow PEP 8 guidelines.
- Use clear and descriptive variable and function names.
- Include docstrings for functions and classes.

## Versioning
- Changes to the CLI should be tracked and reflected in project versioning.
- Coordinate with changes in dependent modules.

## See Also
- [CLI README](README.md)
- [CLI API Reference](api_reference.md)
- [CV Pipeline Developer Guide](../cv_pipeline/developer_guide.md)
- [Database Developer Guide](../db/developer_guide.md)
