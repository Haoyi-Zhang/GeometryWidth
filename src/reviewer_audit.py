"""Static audit of the retained Python artifact.

This checks source-level properties that matter for reproducibility and verifier
separation.  It is not a security certification or a proof of the mathematics.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp", "boto3", "ftplib", "httpx", "paramiko", "requests",
    "selenium", "smtplib", "socket", "subprocess", "urllib.request",
}
FORBIDDEN_CALLS = {"eval", "exec"}
PATH_PATTERNS = (
    re.compile(r"/home/"), re.compile(r"/mnt/"), re.compile(r"[A-Za-z]:\\\\"),
)


class ReviewerAuditError(ValueError):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewerAuditError(message)


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module)
    return roots


def audit(root: Path = ROOT) -> dict:
    files = sorted(
        path for path in root.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    need(files, "no Python sources found")
    scientific_assert_nodes = 0
    test_assert_nodes = 0
    dynamic_calls: list[str] = []
    forbidden_imports: list[str] = []
    private_paths: list[str] = []
    todo_markers: list[str] = []
    imports_by_file: dict[str, list[str]] = {}
    for path in files:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=rel)
        except (SyntaxError, ValueError) as exc:
            raise ReviewerAuditError(f"{rel}: cannot parse/compile: {exc}") from exc
        imports = imported_roots(tree)
        imports_by_file[rel] = sorted(imports)
        count = sum(isinstance(node, ast.Assert) for node in ast.walk(tree))
        if rel.startswith("tests/"):
            test_assert_nodes += count
        else:
            scientific_assert_nodes += count
        for name in imports:
            if name in FORBIDDEN_IMPORT_ROOTS or name.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
                forbidden_imports.append(f"{rel}:{name}")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_CALLS:
                    dynamic_calls.append(f"{rel}:{node.lineno}:{node.func.id}")
        if rel != "src/reviewer_audit.py":
            for pattern in PATH_PATTERNS:
                if pattern.search(text):
                    private_paths.append(f"{rel}:{pattern.pattern}")
        if rel != "src/reviewer_audit.py":
            for number, line in enumerate(text.splitlines(), 1):
                if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line, re.IGNORECASE):
                    todo_markers.append(f"{rel}:{number}")

    need(scientific_assert_nodes == 0, "scientific source contains removable assert statements")
    need(not dynamic_calls, f"dynamic evaluation calls found: {dynamic_calls}")
    need(not forbidden_imports, f"network/process imports found: {forbidden_imports}")
    need(not private_paths, f"private absolute paths found: {private_paths}")
    need(not todo_markers, f"unresolved TODO/FIXME markers found: {todo_markers}")

    producer_independent = ["src/check.py", "src/verify_holdout.py", "report.py"]
    for rel in producer_independent:
        need(rel in imports_by_file, f"missing independent path: {rel}")
        imports = imports_by_file[rel]
        need("produce" not in imports and "src.produce" not in imports,
             f"{rel} imports producer")
    need("exact" not in imports_by_file["src/check.py"],
         "main checker imports producer arithmetic module")

    return {
        "accepted": True,
        "python_source_files": len(files),
        "scientific_removable_assert_nodes": scientific_assert_nodes,
        "pytest_assert_nodes": test_assert_nodes,
        "dynamic_evaluation_calls": len(dynamic_calls),
        "forbidden_network_or_process_imports": len(forbidden_imports),
        "private_absolute_paths": len(private_paths),
        "unresolved_todo_markers": len(todo_markers),
        "producer_independent_paths": producer_independent,
        "scope": "static source audit; not a security certification or mathematical proof",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.root.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
