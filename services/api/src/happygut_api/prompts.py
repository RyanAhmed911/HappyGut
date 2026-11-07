"""Load versioned runtime prompts from prompts/runtime/<id>/v<N>.md (front matter + body)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Prompt:
    id: str
    version: int
    model: str
    temperature: float
    body: str

    @property
    def ref(self) -> str:
        return f"{self.id}@v{self.version}"

    def render(self, **values: str) -> str:
        # Only {name} placeholders are replaced, so JSON braces in values are safe.
        def sub(m: re.Match[str]) -> str:
            key = m.group(1)
            if key not in values:
                raise KeyError(f"{self.ref}: missing value for {{{key}}}")
            return str(values[key])

        return re.sub(r"\{([a-z_]+)\}", sub, self.body)


def load_prompt(prompts_dir: Path, prompt_id: str, version: int | None = None) -> Prompt:
    folder = prompts_dir / prompt_id
    versions = sorted(int(p.stem[1:]) for p in folder.glob("v*.md"))
    if not versions:
        raise FileNotFoundError(f"no versions for prompt {prompt_id} in {folder}")
    v = version if version is not None else versions[-1]
    text = (folder / f"v{v}.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{prompt_id} v{v}: missing front matter")
    meta = yaml.safe_load(m.group(1))
    if meta.get("id") != prompt_id or int(meta.get("version")) != v:
        raise ValueError(f"{prompt_id} v{v}: front matter id/version mismatch")
    return Prompt(prompt_id, v, str(meta.get("model", "")), float(meta.get("temperature", 0.0)), m.group(2).strip())
