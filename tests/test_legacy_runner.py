"""Run legacy assertion scripts under pytest; do not count import-only files as tests."""
import ast
from pathlib import Path
import os
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]


def executable_scripts():
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        tree = ast.parse(path.read_text())
        if any(isinstance(n, ast.If) and "__name__" in ast.unparse(n.test) for n in tree.body):
            yield path


@pytest.mark.parametrize("script", list(executable_scripts()), ids=lambda p: p.stem)
def test_legacy_script(script):
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT,
                            env={**os.environ, "PYTHONPATH": str(ROOT)}, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
