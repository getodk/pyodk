"""
Run linters.

source venv/bin/activate && python bin/pre_commit.py
"""

import os
import sys
from subprocess import PIPE, Popen


def run_linters():
    proj = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    linters = ["black", "isort", "flake8", "pycodestyle"]
    failures = []
    for i, cmd in enumerate(linters):
        with Popen(
            [cmd, "pyodk", "tests", "bin"],
            cwd=proj,
            stdout=PIPE,
            stderr=PIPE,
        ) as proc:
            out = proc.stdout.read().decode("utf-8").strip()
            err = proc.stderr.read().decode("utf-8").strip()
        if 0 < i:
            print("******************************")
        print(f"Ran {cmd}, return code: {proc.returncode}")
        if proc.returncode is not None:
            failures.append(proc.returncode)
        else:
            failures.append(0)
        if 0 < len(out):
            print(out)
        if 0 < len(err):
            print(err)
    if 0 == max(failures):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(run_linters())
