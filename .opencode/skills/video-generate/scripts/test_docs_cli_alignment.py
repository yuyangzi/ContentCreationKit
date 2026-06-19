"""Verify CLI command examples in SKILL.md actually match each script's argparse.

Matches both forms used in SKILL.md:
  - $VENV_PYTHON $SCRIPTS_DIR/<name>.py [flags...]
  - python <name>.py [flags...]
  - python scripts/<name>.py [flags...]
"""
import os
import re
import subprocess
import sys
import pytest

SKILL_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Matches:
#   $VENV_PYTHON $SCRIPTS_DIR/foo.py
#   $VENV_PYTHON path/to/foo.py
#   python foo.py
#   python scripts/foo.py
#   python3 foo.py
INVOCATION_RE = re.compile(
    r"(?:\$VENV_PYTHON|python3?)\s+"           # interpreter token
    r"(?:[^\s`]*?/)?"                           # optional path prefix
    r"(\w+\.py)"                                # script name (capture 1)
    r"((?:\s+(?:\\\s*\n\s*)?[^\n`]*)*)",        # everything until end of line/block (capture 2)
    re.MULTILINE,
)


def _extract_python_invocations(md_path):
    """Return a list of (script_name, [flags...]) from SKILL.md."""
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    invocations = []
    for match in INVOCATION_RE.finditer(text):
        script = match.group(1)
        rest = match.group(2) or ""
        flags = re.findall(r"--[a-zA-Z][a-zA-Z0-9-]*", rest)
        invocations.append((script, flags))
    return invocations


def _get_script_help(script_name):
    """Run script with --help and return stdout+stderr."""
    path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(path):
        return ""
    result = subprocess.run(
        [sys.executable, path, "--help"],
        capture_output=True, text=True, timeout=15,
    )
    return result.stdout + result.stderr


def test_skill_md_has_python_invocations():
    """SKILL.md must contain at least one parseable script invocation."""
    invocations = _extract_python_invocations(SKILL_MD)
    assert invocations, (
        "No python invocations parsed from SKILL.md. "
        "Either SKILL.md lacks command examples, or INVOCATION_RE needs an update."
    )
    # Sanity: must mention all four Part 1 scripts at least once
    script_names = {s for s, _ in invocations}
    expected = {"scenes_schema.py", "generate_audio.py",
                "fetch_assets.py", "merge_scenes.py"}
    missing = expected - script_names
    assert not missing, f"SKILL.md missing invocation examples for: {missing}"


def test_skill_md_python_invocations_use_known_flags():
    """Every --flag in a python invocation in SKILL.md must be recognized
    by the corresponding script's argparse."""
    invocations = _extract_python_invocations(SKILL_MD)
    failures = []
    for script, flags in invocations:
        if not flags:
            continue
        help_text = _get_script_help(script)
        if not help_text:
            failures.append(f"{script}: --help failed or script missing")
            continue
        for flag in flags:
            if flag not in help_text:
                failures.append(
                    f"{script}: flag {flag} not in argparse --help"
                )

    assert not failures, "CLI/docs drift:\n" + "\n".join(failures)
