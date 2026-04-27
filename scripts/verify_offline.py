#!/usr/bin/env python3
"""
Verify that the offline-fork neutering is still in place after merging upstream.
Run this script after `git merge upstream/main` or `git rebase upstream/main`.

Usage:
    python scripts/verify_offline.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()

# Files that are fully disabled and protected by .gitattributes merge=ours.
FULLY_DISABLED = [
    REPO_ROOT / "aider" / "versioncheck.py",
    REPO_ROOT / "aider" / "openrouter.py",
    REPO_ROOT / "aider" / "scrape.py",
    REPO_ROOT / "aider" / "report.py",
    REPO_ROOT / "aider" / "help.py",
]

# Partially modified files: we check key functions for early returns / noops.
PARTIAL_CHECKS = {
    "aider/analytics.py": {
        "Analytics.__init__": "permanently_disable = True",
    },
    "aider/models.py": {
        "ModelInfoManager._update_cache": "pass",
    },
    "aider/onboarding.py": {
        "check_openrouter_tier": "return True",
        "offer_openrouter_oauth": "return False",
        "exchange_code_for_key": "return None",
    },
    "aider/main.py": {
        "check_streamlit_install": "return False",
    },
}


def _func_body(file_path: Path, func_name: str) -> str:
    """Return the first ~800 chars after the function definition."""
    source = file_path.read_text(encoding="utf-8")
    # Support simple "def func_name(" or "class C: def func_name("
    pattern = f"def {func_name}("
    idx = source.find(pattern)
    if idx == -1:
        return ""
    return source[idx : idx + 800]


def check_fully_disabled() -> bool:
    ok = True
    for p in FULLY_DISABLED:
        if not p.exists():
            print(f"⚠️  {p.name} does not exist – unexpected, but skipping.")
            continue
        text = p.read_text(encoding="utf-8")
        # Quick heuristic: these files should contain early returns / noops
        # and should NOT contain active network calls.
        bad = [kw for kw in ("requests.get", "urllib.request", "webbrowser.open") if kw in text]
        if bad:
            print(f"❌ {p.name}: still contains active network calls {bad}")
            ok = False
        else:
            print(f"✅ {p.name}: no active network calls detected")
    return ok


def check_partial() -> bool:
    ok = True
    for rel_path, funcs in PARTIAL_CHECKS.items():
        file_path = REPO_ROOT / rel_path
        if not file_path.exists():
            print(f"⚠️  {rel_path} missing – skipping")
            continue
        for func_name, expected in funcs.items():
            body = _func_body(file_path, func_name)
            if not body:
                print(f"❌ {rel_path}: function '{func_name}' not found")
                ok = False
                continue
            if expected in body:
                print(f"✅ {rel_path}: {func_name} → contains '{expected}'")
            else:
                print(f"❌ {rel_path}: {func_name} → missing '{expected}' (upstream may have changed it)")
                ok = False
    return ok


def main() -> int:
    print("=" * 60)
    print("Offline-fork verification")
    print("=" * 60)
    print()

    ok1 = check_fully_disabled()
    print()
    ok2 = check_partial()
    print()

    if ok1 and ok2:
        print("🎉 All offline checks passed.")
        return 0
    else:
        print("⚠️  Some checks failed. Please resolve conflicts before pushing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
