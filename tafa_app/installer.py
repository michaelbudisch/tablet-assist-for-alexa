"""Safe TAFA App installer for a single public Home Assistant integration.

Never touches configuration.yaml, .storage, private dashboards or separately
managed Marketplace/manual integrations. App-owned upgrades are staged, verified,
swapped atomically and backed up for rollback.
"""
import ast
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

DOMAIN = "tablet_assist_for_alexa"
DOMAINS = (DOMAIN,)
MARKER = ".tafa-managed.json"

def _files(root):
    result = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlinks are not allowed in a managed integration")
        if not path.is_file() or path.name == MARKER or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result

def _managed(root):
    path = root / MARKER
    if not path.is_file() or path.is_symlink():
        return False
    try:
        marker = json.loads(path.read_text(encoding="utf-8"))
        return marker.get("schema") == 1 and marker.get("domain") == DOMAIN and marker.get("files") == _files(root)
    except (OSError, ValueError, TypeError):
        return False

def _verified_tafa_source(dest):
    """Conservatively identify this project's previously unmanaged install.

    Opt-in adoption is the only path for a modified or markerless copy.
    The existing directory is always preserved as a complete rollback.
    """
    if not dest.is_dir() or dest.is_symlink():
        return False
    try:
        manifest=json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
        return (manifest.get("domain")==DOMAIN
                and "@michaelbudisch" in manifest.get("codeowners", [])
                and str(manifest.get("documentation", "")).startswith(
                    "https://github.com/michaelbudisch/tablet-assist-for-alexa/")
                and (dest/"__init__.py").is_file()
                and not (dest/"__init__.py").is_symlink())
    except (OSError, ValueError, TypeError):
        return False


def _prepare(source, dest):
    if not source.is_dir() or source.is_symlink():
        raise ValueError("Incomplete bundled integration.")
    for f in source.rglob("*"):
        if f.is_symlink():
            raise ValueError("Unexpected bundled symlink.")
        if not f.is_file():
            continue
        if "__pycache__" in f.parts or f.suffix == ".pyc" or f.name == MARKER:
            continue
        target = dest / f.relative_to(source)
        target.parent.mkdir(parents=True,exist_ok=True)
        if f.suffix in (".py", ".json", ".yaml", ".js"):
            content = f.read_text(encoding="utf-8")
            if f.suffix == ".py":
                ast.parse(content,filename=str(f))
            if f.suffix == ".json":
                json.loads(content)
            target.write_text(content,encoding="utf-8")
        else:
            shutil.copyfile(f,target)
    manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("domain") != DOMAIN or not manifest.get("version"):
        raise ValueError("Unexpected integration domain or version")
    (dest / MARKER).write_text(json.dumps({
        "schema": 1, "domain": DOMAIN,
        "version": manifest["version"], "files": _files(dest)
    },sort_keys=True),encoding="utf-8")

def status(config):
    root=config / "custom_components"
    path=root / DOMAIN
    if root.is_symlink() or path.is_symlink():
        return {DOMAIN:"existing (not managed)"}
    if not path.exists():
        return {DOMAIN:"not installed"}
    if not path.is_dir():
        return {DOMAIN:"invalid installation"}
    try:
        version=json.loads((path/"manifest.json").read_text(encoding="utf-8"))["version"]
    except (OSError,ValueError,KeyError,TypeError):
        return {DOMAIN:"existing (version unknown)"}
    return {DOMAIN:"installed · "+str(version)+(" · managed by TAFA App" if _managed(path) else " · external/manual installation")}

def install(config, bundle, values=None, domains=DOMAINS, adopt_existing=False):
    """Add missing files or safely update an unchanged TAFA-managed installation.

    For HACS-managed/manual installations, return without mutation.
    """
    if tuple(domains) != DOMAINS:
        raise ValueError("Invalid component selection")
    if not config.is_dir() or config.is_symlink():
        raise ValueError("Home Assistant configuration mount is missing")
    root=config / "custom_components"
    if root.is_symlink():
        raise ValueError("Refusing symbolic-link destination")
    root.mkdir(exist_ok=True)
    if not root.is_dir():
        raise ValueError("Invalid custom_components directory")
    dest=root / DOMAIN
    if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
        return []
    if dest.exists() and not _managed(dest):
        if adopt_existing is not True or not _verified_tafa_source(dest):
            return []
    with tempfile.TemporaryDirectory(prefix=".tafa-stage-",dir=root) as tmp:
        stage=Path(tmp) / DOMAIN
        stage.mkdir()
        _prepare(bundle/DOMAIN,stage)
        if dest.exists():
            if _files(stage)==_files(dest):
                return []
            backup_dir=config / ".tafa" / "rollback"
            backup_dir.mkdir(parents=True,exist_ok=True)
            backup=backup_dir / (DOMAIN+"-"+uuid4().hex)
            os.replace(dest,backup)
            try:
                os.replace(stage,dest)
            except OSError:
                os.replace(backup,dest)
                raise
            return [DOMAIN+" (updated; previous version backed up)"]
        try:
            os.replace(stage,dest)
        except OSError:
            raise
        return [DOMAIN]

def bootstrap(config,bundle,adopt_existing=False):
    """Default: protect manual installs. One-time verified adoption needs opt-in."""
    return install(config,bundle,adopt_existing=adopt_existing)
