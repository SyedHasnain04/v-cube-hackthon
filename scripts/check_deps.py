"""
scripts/check_deps.py — confirm torch is absent from the installed environment.
Run this at build time (after pip install) to catch accidental torch re-introduction.

Exit code 0 = clean.  Exit code 1 = torch (or sentence-transformers) found.
"""

import importlib.util
import sys

BANNED = ["torch", "sentence_transformers", "transformers"]
REQUIRED = ["fastembed", "faiss", "numpy", "psutil"]

failed = False

print("=== Athenaeum dependency audit ===")

for pkg in BANNED:
    spec = importlib.util.find_spec(pkg)
    if spec is not None:
        print(f"[FAIL] Banned package present: {pkg}")
        failed = True
    else:
        print(f"[OK]   Absent (expected): {pkg}")

for pkg in REQUIRED:
    spec = importlib.util.find_spec(pkg)
    if spec is None:
        print(f"[FAIL] Required package missing: {pkg}")
        failed = True
    else:
        print(f"[OK]   Present (expected): {pkg}")

if failed:
    print("\nDependency audit FAILED — fix requirements.txt and rebuild.")
    sys.exit(1)
else:
    print("\nDependency audit PASSED.")
    sys.exit(0)
