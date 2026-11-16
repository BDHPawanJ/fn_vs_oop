# Contributing

## Adding a new example

1. Create matching files in both `functional/` and `oop/` subdirectories
   of the relevant section (`core_concepts/`, `shared_lib/`, `advanced_concepts/`).
2. Both files must demonstrate the **same behaviour** so the contrast is clear.
3. Add tests in the corresponding `tests/` folder.
4. Add a demo section in `compare.py` with an `insight()` line explaining
   the key difference.

## Running tests before pushing

```bash
python3 -m pytest
```

All 174 tests must pass.

## Code style

- No external dependencies — stdlib only.
- Each source file must have a module docstring explaining:
  the concept, when to use it, and the key contrast with the other paradigm.
- No use of the words "simple" or "senior" in any file.
- Maximum ~80 lines per source file (compare.py and mixed.py are exceptions).
