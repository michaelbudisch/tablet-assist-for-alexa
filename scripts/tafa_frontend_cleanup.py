#!/usr/bin/env python3
"""Audit and safely archive obsolete private TAFA frontend builds.

Dry-run by default. --apply requires the real HA resource registry, creates a
verified ZIP outside www/, and only then deletes superseded text assets.
No Home Assistant .storage data is ever edited.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile, ZIP_DEFLATED

FOLDERS = (
    "www",
    "www/tafa",
    "www/tafa/modules",
    "www/tafa/modules/voice",
    "www/tafa-home",
)
VERSIONED = re.compile(r"^(?P<stem>.+)-v(?P<version>\d+(?:\.\d+){1,3})\.(?P<ext>js|css)$")
FRONTEND = "custom_components/tablet_assist_for_alexa/frontend"
BUNDLE = "tafa_app/bundle/tablet_assist_for_alexa/frontend"


def version_key(path: Path) -> tuple[int, ...]:
    match = VERSIONED.fullmatch(path.name)
    return tuple(int(part) for part in match["version"].split(".")) if match else ()


def resources(config: Path) -> list[str] | None:
    """Read the HA-managed resource registry without modifying it."""
    path = config / ".storage" / "lovelace_resources"
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("data", {}).get("items")
    if not isinstance(items, list):
        return None
    return [item.get("url", "") for item in items if isinstance(item, dict)]


def plan(config: Path, keep_rollback: int = 1) -> dict:
    root = config.resolve()
    www = root / "www"
    if not www.is_dir():
        raise ValueError(f"Home Assistant www/ folder not found: {www}")
    if keep_rollback < 1:
        raise ValueError("Keep at least one rollback version per family")
    manifest_path = www / "tafa" / "frontend-build.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    live_resources = resources(root)
    # Keep any file named in an active Lovelace resource or the build manifest.
    references = json.dumps(manifest, ensure_ascii=False) + "\n"
    references += "\n".join(live_resources or []) + "\n"
    grouped: dict[tuple[str, str, str], list[Path]] = defaultdict(list)
    for name in FOLDERS:
        directory = root / name
        if not directory.is_dir():
            continue
        for file in directory.iterdir():
            if not file.is_file() or file.is_symlink():
                continue
            match = VERSIONED.fullmatch(file.name)
            if match:
                grouped[(name, match["stem"], match["ext"])].append(file)
            elif file.suffix in (".js", ".json", ".css", ".html"):
                # Scan stable modules and entrypoints for dynamic imports too.
                references += file.read_text(encoding="utf-8") + "\n"
    remove = []
    protected = []
    for (directory, stem, ext), builds in sorted(grouped.items()):
        stable = root / directory / f"{stem}.{ext}"
        if not stable.is_file() or stable.is_symlink():
            protected.extend((f, "no stable entrypoint") for f in builds)
            continue
        builds.sort(key=version_key, reverse=True)
        for idx, file in enumerate(builds):
            if idx < keep_rollback:
                protected.append((file, "rollback"))
            elif file.name in references or file.as_posix().replace(root.as_posix() + "/www/", "/local/") in references:
                protected.append((file, "still referenced"))
            else:
                remove.append(file)
    # A resource/manifest mismatch previously caused endless "update" prompts.
    version = str(manifest.get("version", ""))
    main = str(manifest.get("main", ""))
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Invalid frontend-build.json version")
    if f"?v={version}" not in main:
        raise ValueError("frontend-build.json main URL does not match build version")
    resource_ok = bool(live_resources and main in live_resources)
    return {
        "remove": remove,
        "protected": protected,
        "resources_read": live_resources is not None,
        "resource_matches_manifest": resource_ok,
        "version": version,
    }


def archive_and_remove(config: Path, candidates: list[Path]) -> Path | None:
    if not candidates:
        return None
    root = config.resolve()
    target = root / "backups"
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = target / f"tafa-frontend-legacy-{stamp}.zip"
    if archive.exists():
        raise FileExistsError(archive)
    contents = {}
    with ZipFile(archive, "x", compression=ZIP_DEFLATED, compresslevel=9) as zipfile:
        for file in candidates:
            if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(root / "www"):
                raise ValueError(f"Unsafe cleanup path: {file}")
            relative = file.relative_to(root).as_posix()
            contents[relative] = hashlib.sha256(file.read_bytes()).hexdigest()
            zipfile.write(file, relative)
        zipfile.writestr("tafa-archive-manifest.json", json.dumps({
            "schema": 1, "version": 1, "sha256": contents,
            "restore": "Extract this ZIP to the original Home Assistant config directory",
        }, indent=2))
    # Do not delete even one original unless the archive reopens and verifies.
    with ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError("Backup ZIP failed CRC verification")
        for name, checksum in contents.items():
            if hashlib.sha256(z.read(name)).hexdigest() != checksum:
                raise RuntimeError(f"Backup SHA-256 verification failed: {name}")
    for file in candidates:
        file.unlink()
    return archive


def repo_check(base: Path) -> int:
    shipped = base / FRONTEND
    bundled = base / BUNDLE
    errors = []
    for directory in (shipped, bundled):
        if not directory.is_dir():
            errors.append(f"Missing frontend: {directory}")
            continue
        for file in directory.iterdir():
            if VERSIONED.fullmatch(file.name):
                errors.append(f"Shipped frontend contains a versioned filename: {file}")
    for relative in ("dashboard.js", "dashboard_model.js", "panel.js", "voice_tools.js"):
        a, b = shipped / relative, bundled / relative
        if not a.is_file() or not b.is_file() or a.read_bytes() != b.read_bytes():
            errors.append(f"Delivery mirrors diverged: {relative}")
    for problem in errors:
        print("ERROR:", problem, file=sys.stderr)
    if not errors:
        print("OK: public TAFA frontend uses stable names and matching delivery mirrors")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Home Assistant configuration directory")
    parser.add_argument("--apply", action="store_true", help="Archive then delete safe obsolete files")
    parser.add_argument("--keep-rollback", type=int, default=1)
    parser.add_argument("--repo-check", action="store_true", help="Check public GitHub delivery assets")
    args = parser.parse_args()
    if args.repo_check:
        return repo_check(Path(__file__).resolve().parents[1])
    if not args.config:
        parser.error("--config is required unless --repo-check is used")
    result = plan(args.config, args.keep_rollback)
    to_remove = result["remove"]
    for file in to_remove:
        print("obsolete:", file.relative_to(args.config.resolve()))
    print(f"Build: {result['version']} | obsolete: {len(to_remove)} | protected: {len(result['protected'])}")
    if not args.apply:
        print("DRY RUN. No files changed. Re-run with --apply for verified ZIP backup and removal.")
        return 0
    if not result["resources_read"] or not result["resource_matches_manifest"]:
        print("ABORT: Lovelace resource registry unavailable or current manifest is not registered.", file=sys.stderr)
        return 2
    archive = archive_and_remove(args.config, to_remove)
    print(f"Archived and removed {len(to_remove)} files; backup: {archive or 'not needed'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
