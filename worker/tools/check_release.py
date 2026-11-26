"""Worker release gate and opt-in secret-safe ZIP builder.

Run: python worker/tools/check_release.py [--package /path/to/output.zip]
"""
import argparse
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {".py", ".md", ".yaml", ".yml", ".json", ".txt", ".ps1", ".sh",
           ".service", ".template", ".bat"}
ALLOWED_NAMES = {".gitignore", "Dockerfile", "VERSION"}
EXCLUDE = {".env", ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
           ".venv", "venv", "node_modules", "GPU-Worker-Verbindungsdaten.txt",
           "tafa-worker.json", ".tafa-worker-id"}
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def validate():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not VERSION_RE.fullmatch(version):
        raise RuntimeError("VERSION must contain one semver value")
    for name in ("README.md", "docs/README.md", "docs/README.de.md"):
        title = (ROOT / name).read_text(encoding="utf-8").splitlines()[0]
        if version not in title:
            raise RuntimeError(f"{name} heading does not contain {version}")
    for name in ("docs/CHANGELOG.md", "docs/CHANGELOG.de.md"):
        if f"## {version}" not in (ROOT / name).read_text(encoding="utf-8"):
            raise RuntimeError(f"{name} lacks changelog entry {version}")
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    for service in ("vision", "qwen-stream", "ops"):
        if f"image: jarvis-{service}:{version}" not in compose:
            raise RuntimeError(f"compose image tag for {service} is not {version}")
    # All public worker health/capability version fields follow the release.
    runtime_versions = {
        "ops/server.py": f'VERSION = "{version}"',
        "qwen-stream/server.py": f"worker_version='{version}'",
        "vision/server.py": f'worker_version="{version}"',
    }
    for name, marker in runtime_versions.items():
        if marker not in (ROOT / name).read_text(encoding="utf-8"):
            raise RuntimeError(f"{name} reports a different worker version")
    return version


def safe_files():
    for path in sorted(ROOT.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"Symlinks are not accepted: {path.relative_to(ROOT)}")
        if not path.is_file():
            continue
        parts = path.relative_to(ROOT).parts
        if any(p in EXCLUDE or p.startswith(".env") or p.endswith((".wav", ".pcm", ".zip", ".key", ".pem"))
               for p in parts):
            continue
        if path.suffix not in ALLOWED and path.name not in ALLOWED_NAMES:
            continue
        if path.stat().st_size > 2 * 1024 * 1024:
            raise RuntimeError(f"Unexpectedly large file: {path.relative_to(ROOT)}")
        yield path


def package(target):
    target = Path(target).resolve()
    if ROOT in target.parents or target == ROOT:
        raise RuntimeError("Release ZIP must be outside worker source tree")
    target.parent.mkdir(parents=True, exist_ok=True)
    version = validate()
    files = list(safe_files())
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zipfile_out:
        for path in files:
            zipfile_out.write(path, f"jarvis_gpu_worker_{version}/" + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as check:
        names = check.namelist()
        if any("/.env" in n or n.endswith((".wav", ".pcm", ".key", ".pem")) for n in names):
            target.unlink(missing_ok=True)
            raise RuntimeError("Sensitive file leaked into package")
    return target, len(files)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", metavar="ZIP")
    args = parser.parse_args()
    print("Jarvis GPU Worker", validate(), "- release metadata OK")
    if args.package:
        target, count = package(args.package)
        print(f"Safe release package: {target} ({count} files)")


if __name__ == "__main__":
    main()
