#!/usr/bin/env python3
"""
Verify that the offline-fork neutering is still in place after merging upstream.
Run this script after `git merge upstream/main` or `git rebase upstream/main`.

Usage:
    python scripts/verify_offline.py
"""

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()

# Files that are fully disabled and protected by .gitattributes merge=ours.
FULLY_DISABLED = [
    REPO_ROOT / "aider" / "openrouter.py",
    REPO_ROOT / "aider" / "scrape.py",
    REPO_ROOT / "aider" / "report.py",
    REPO_ROOT / "aider" / "help.py",
]

# Partially modified files: we check key functions for early returns / noops.
PARTIAL_CHECKS = {
    "aider/analytics.py": {
        "Analytics.__init__": "self.disable(True)",
    },
    "aider/models.py": {
        "ModelInfoManager._update_cache": "self.content = self.content or {}",
        "Model.github_copilot_token_to_open_ai_key": "disabled in offline mode",
    },
    "aider/onboarding.py": {
        "check_openrouter_tier": "return True",
        "offer_openrouter_oauth": "return False",
        "exchange_code_for_key": "return None",
    },
    "aider/main.py": {
        "check_streamlit_install": "return False",
        "reject_online_feature": "disabled in offline mode",
        "validate_offline_model": "Offline mode only allows local or intranet models.",
    },
    "aider/versioncheck.py": {
        "check_version": "disabled in offline mode",
        "install_upgrade": "disabled in offline mode",
        "install_from_main_branch": "disabled in offline mode",
    },
}


def _ast_body_segment(source: str, node: ast.AST) -> str:
    start = getattr(node, "lineno", None)
    end = getattr(node, "end_lineno", None)
    if start is None:
        return ""

    lines = source.splitlines()
    if end is None:
        end = min(start + 40, len(lines))
    return "\n".join(lines[start - 1 : end])


def _find_qualified_node(tree: ast.AST, dotted_name: str):
    parts = dotted_name.split(".")

    def walk(nodes, remaining):
        if not remaining:
            return None

        target = remaining[0]
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == target:
                if len(remaining) == 1:
                    return node
            elif isinstance(node, ast.ClassDef) and node.name == target:
                if len(remaining) == 1:
                    return node
                found = walk(node.body, remaining[1:])
                if found is not None:
                    return found
        return None

    return walk(getattr(tree, "body", []), parts)


def _func_body(file_path: Path, func_name: str) -> str:
    """Return the source segment for a function/method definition."""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    node = _find_qualified_node(tree, func_name)
    if node is None:
        return ""
    return _ast_body_segment(source, node)


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
