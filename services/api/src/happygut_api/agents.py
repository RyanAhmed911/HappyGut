"""Perception and explanation agents (Pydantic-AI). They perceive and explain; they never decide.

Each agent runs on a primary model with a fallback (FallbackModel), so a free-tier quota
running out doesn't stop the flow (spec 002 FR-012).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Generic, Literal, Protocol, TypeVar

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic import BaseModel, Field  # noqa: E402
from pydantic_ai import Agent, BinaryContent  # noqa: E402
from pydantic_ai.models import Model  # noqa: E402
from pydantic_ai.models.fallback import FallbackModel  # noqa: E402

from .images import CleanImage  # noqa: E402
from .prompts import Prompt  # noqa: E402

T = TypeVar("T")

LANGUAGE_NAMES = {"bn": "Bangla (Bengali script)", "en": "English"}
DIAGNOSIS_TEXT = {"CD": "Crohn's disease", "UC": "ulcerative colitis"}


# ---------------------------------------------------------------- outputs

class PerceivedItem(BaseModel):
    name_en: str = Field(min_length=1, max_length=80)
    name_bn: str | None = Field(default=None, max_length=80)
    confidence: float = Field(ge=0.0, le=1.0)
    preparation: str | None = Field(default=None, max_length=60)
    portion: Literal["small", "medium", "large"] | None = None


class Perception(BaseModel):
    is_food: bool
    items: list[PerceivedItem] = Field(default_factory=list, max_length=12)
    label_text: str | None = Field(default=None, max_length=2000)
    clarifying_question: str | None = Field(default=None, max_length=200)


class DishExplanation(BaseModel):
    dish_id: str
    text: str = Field(min_length=1, max_length=600)
    cited_ids: list[str] = Field(default_factory=list)


class Explanation(BaseModel):
    dishes: list[DishExplanation]
    summary: str = Field(min_length=1, max_length=300)


@dataclass(frozen=True)
class AgentRun(Generic[T]):
    output: T
    model: str
    prompt: str  # "<id>@v<N>"


class Perceiver(Protocol):
    async def perceive(self, *, text: str | None, image: CleanImage | None, lang: str) -> AgentRun[Perception]: ...


class Explainer(Protocol):
    async def explain(self, *, packet: dict, lang: str, diagnosis: str) -> AgentRun[Explanation]: ...


# ---------------------------------------------------------------- models

def build_model(names: list[str], gemini_api_key: str, groq_api_key: str) -> Model:
    """Gemini names go to Google AI Studio, everything else to Groq. Names without a key are skipped."""
    models: list[Model] = []
    for name in names:
        if not name:
            continue
        if name.startswith("gemini"):
            if not gemini_api_key:
                continue
            from pydantic_ai.models.google import GoogleModel
            from pydantic_ai.providers.google import GoogleProvider

            models.append(GoogleModel(name, provider=GoogleProvider(api_key=gemini_api_key)))
        else:
            if not groq_api_key:
                continue
            from pydantic_ai.models.groq import GroqModel
            from pydantic_ai.providers.groq import GroqProvider

            models.append(GroqModel(name, provider=GroqProvider(api_key=groq_api_key)))
    if not models:
        raise RuntimeError(f"no usable model among {names}: set GEMINI_API_KEY and/or GROQ_API_KEY")
    return models[0] if len(models) == 1 else FallbackModel(*models)


# ---------------------------------------------------------------- agents

class PydanticPerceiver:
    def __init__(self, model: Model, prompt: Prompt, timeout_s: float = 20.0):
        self.model, self.prompt, self.timeout_s = model, prompt, timeout_s
        self.agent = Agent(output_type=Perception, retries=1)

    async def perceive(self, *, text: str | None, image: CleanImage | None, lang: str) -> AgentRun[Perception]:
        content: list = []
        if text:
            content.append(f"<user_text>\n{text}\n</user_text>")
        if image is not None:
            content.append(BinaryContent(data=image.data, media_type=image.media_type))
        if not content:
            raise ValueError("perception needs text or an image")
        result = await self.agent.run(
            content,
            model=self.model,
            instructions=self.prompt.render(language=LANGUAGE_NAMES[lang]),
            model_settings={"temperature": self.prompt.temperature},
            timeout=self.timeout_s,
        )
        return AgentRun(result.output, result.response.model_name or "unknown", self.prompt.ref)


class PydanticExplainer:
    def __init__(self, model: Model, prompt: Prompt, timeout_s: float = 20.0):
        self.model, self.prompt, self.timeout_s = model, prompt, timeout_s
        self.agent = Agent(output_type=Explanation, retries=1)

    async def explain(self, *, packet: dict, lang: str, diagnosis: str) -> AgentRun[Explanation]:
        instructions = self.prompt.render(
            packet=json.dumps(packet, ensure_ascii=False, indent=1),
            language_name=LANGUAGE_NAMES[lang],
            diagnosis_text=DIAGNOSIS_TEXT.get(diagnosis, "inflammatory bowel disease"),
        )
        result = await self.agent.run(
            "Write the explanation.",
            model=self.model,
            instructions=instructions,
            model_settings={"temperature": self.prompt.temperature},
            timeout=self.timeout_s,
        )
        return AgentRun(result.output, result.response.model_name or "unknown", self.prompt.ref)
