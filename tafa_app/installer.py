"""Install only bundled public components; never overwrite existing components."""
import ast
import json
import re
import shutil
import tempfile
from pathlib import Path

DOMAINS = ("tablet_assist_for_alexa", "jarvis_tablet_audio")
FIELDS = ("cpu_host", "gpu_host", "cpu_stt", "gpu_stt", "llm_agent")
HOST = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}\Z")
ENTITY = re.compile(r"[a-z0-9_]+\.[a-z0-9_]+\Z")

def replacements(values):
    cpu = values.get("cpu_host", "").strip()
    gpu = values.get("gpu_host", "").strip() or cpu
    stt = values.get("cpu_stt", "").strip()
    gpu_stt = values.get("gpu_stt", "").strip() or stt
    llm = values.get("llm_agent", "").strip() or "conversation.home_assistant"
    if not all(HOST.fullmatch(v) for v in (cpu, gpu)):
        raise ValueError("Enter valid hostnames or IPv4 addresses (without scheme or port).")
    if not all(ENTITY.fullmatch(v) for v in (stt, gpu_stt, llm)) or not stt.startswith("stt.") or not gpu_stt.startswith("stt.") or not llm.startswith("conversation."):
        raise ValueError("Enter valid STT and conversation entity IDs.")
    return dict(zip(("__JARVIS_CPU_HOST__", "__JARVIS_GPU_HOST__", "__JARVIS_CPU_STT__", "__JARVIS_GPU_STT__", "__JARVIS_LLM_AGENT__", "__JARVIS_PIPELINE_ID__"), (cpu, gpu, stt, gpu_stt, llm, "")))

def status(config):
    root = config / "custom_components"
    result = {}
    for domain in DOMAINS:
        p = root / domain
        if root.is_symlink() or p.is_symlink():
            result[domain] = "existing (not managed)"
        elif not p.exists():
            result[domain] = "not installed"
        else:
            try:
                result[domain] = "installed · " + str(json.loads((p / "manifest.json").read_text())["version"])
            except (OSError, ValueError, KeyError, TypeError):
                result[domain] = "existing (version unknown)"
    return result

def install(config, bundle, values, domains=DOMAINS):
    """Stage validated components. Install new ones only; never update existing folders."""
    if not domains or any(d not in DOMAINS for d in domains):
        raise ValueError("Invalid component selection")
    root = config / "custom_components"
    if root.is_symlink():
        raise ValueError("Refusing symbolic-link destination.")
    if not config.is_dir():
        raise ValueError("Home Assistant configuration mount is missing.")
    root.mkdir(exist_ok=True)
    if not root.is_dir():
        raise ValueError("Invalid custom_components directory.")
    pending = [d for d in domains if not (root / d).exists() and not (root / d).is_symlink()]
    if not pending:
        return []
    # The base integration is host-independent. Legacy audio needs explicit validated hosts.
    repl = replacements(values) if "jarvis_tablet_audio" in pending else {}
    # Build and validate every new component before publishing any directory.
    with tempfile.TemporaryDirectory(prefix=".tafa-stage-", dir=root) as tmp:
        stage = Path(tmp)
        for domain in pending:
            src = bundle / domain
            target = stage / domain
            if not (src / "manifest.json").is_file():
                raise ValueError("Incomplete bundled integration.")
            for f in src.rglob("*"):
                if f.is_symlink():
                    raise ValueError("Unexpected bundled symbolic link.")
                if not f.is_file():
                    continue
                out = target / f.relative_to(src)
                out.parent.mkdir(parents=True, exist_ok=True)
                if f.suffix in (".py", ".json", ".yaml", ".js"):
                    content = f.read_text(encoding="utf-8")
                    if domain == "jarvis_tablet_audio":
                        for key, value in repl.items():
                            content = content.replace(key, value)
                        if f.name == "const.py":
                            content = content.replace(":10501", ":10502")
                        if "__JARVIS_" in content:
                            raise ValueError("Unresolved configuration placeholder: " + f.name)
                    if f.suffix == ".py":
                        ast.parse(content, filename=str(f))
                    if f.suffix == ".json":
                        json.loads(content)
                    out.write_text(content, encoding="utf-8")
                else:
                    shutil.copyfile(f, out)
            if json.loads((target / "manifest.json").read_text())["domain"] != domain:
                raise ValueError("Unexpected integration domain.")
        installed = []
        for domain in pending:
            dest = root / domain
            # mkdir is exclusive: never replace a pre-existing directory.
            try:
                dest.mkdir()
            except FileExistsError:
                continue
            try:
                shutil.copytree(stage / domain, dest, dirs_exist_ok=True)
            except Exception:
                # Only remove the directory created by this invocation.
                shutil.rmtree(dest)
                raise
            installed.append(domain)
        return installed


def bootstrap(config, bundle):
    """Provision the standalone base integration when the TAFA App first starts.

    Never overwrite an existing Marketplace-managed or manually installed integration.
    The optional legacy backend remains an explicit configuration choice until merged.
    """
    return install(config, bundle, {}, domains=("tablet_assist_for_alexa",))
