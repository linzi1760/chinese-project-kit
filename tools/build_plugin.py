#!/usr/bin/env python3
"""Build a deterministic, skills-only plugin ZIP without mutating source/state."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


SKILL_FILES = (
    "SKILL.md", "agents/openai.yaml", "assets/项目包规范.json",
    "references/Flowkit映射.md", "references/场景与交付.md",
    "references/自动接续与验收.md", "scripts/project_kit.py",
    "scripts/project_kit_agent.py",
)


def build(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    manifest = json.loads((source / "packaging/plugin.json").read_text(encoding="utf-8"))
    if manifest.get("name") != "chinese-project-kit":
        raise ValueError("Unexpected plugin identity")
    entries = {
        "plugin.json": source / "packaging/plugin.json",
        "README.md": source / "packaging/README.md",
        "LICENSE": source / "LICENSE",
    }
    entries.update({"skills/chinese-project-kit/" + name: source / name for name in SKILL_FILES})
    payload = {}
    for name, path in entries.items():
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(source):
            raise ValueError(f"Unsafe or missing package input: {name}")
        payload[name] = path.read_bytes()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation: never overwrite a delivered package or user file.
    with output.open("xb") as target:
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, content in sorted(payload.items()):
                info = zipfile.ZipInfo(name, date_time=(2026, 10, 28, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content)
    return {"path": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "files": len(payload), "version": manifest["version"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), ensure_ascii=False))
