"""Check the AI model setup: is each key read, and does each configured model answer?

    uv run python -m happygut_api.diagnose                 # text + a generated test image
    uv run python -m happygut_api.diagnose my_plate.jpg    # text + your photo
    uv run python -m happygut_api.diagnose --model gemini-2.5-flash
    uv run python -m happygut_api.diagnose --list          # the models each key can use

Every model in the fallback chain is called on its own, so the output shows which one
fails and why (the provider's own error message). Key values are never printed.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import sys
import time
from pathlib import Path

from . import model_catalog
from .agents import PydanticExplainer, PydanticPerceiver, build_model, describe_error
from .images import ImageRejected, sanitise
from .prompts import load_prompt
from .settings import get_settings

PACKET = {"dishes": [{
    "dish_id": "dish.kacchi_biryani", "name": "Kacchi biryani", "main_reason": "guideline", "alternative": "Plain rice",
    "evidence": [
        {"id": "dish:dish.kacchi_biryani", "type": "composition", "text": "Typical recipe of Kacchi biryani: high fat (high)."},
        {"id": "RC-TEST", "type": "guideline", "component": "fat", "title": "Limit high-fat food in a flare",
         "recommendation": "During a flare, choose lower-fat dishes.", "strict_rule": False, "sources": ["Test citation."]},
    ],
}]}


def _test_image() -> bytes:
    """A simple drawn plate: rice and a curry. Not a real photo; enough to prove a vision call works."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (512, 512), (235, 228, 214))
    d = ImageDraw.Draw(img)
    d.ellipse((40, 40, 472, 472), fill=(250, 250, 250), outline=(200, 200, 200), width=6)
    d.ellipse((110, 150, 290, 330), fill=(245, 240, 225))  # rice
    d.ellipse((260, 190, 410, 340), fill=(196, 120, 40))  # curry
    out = io.BytesIO()
    img.save(out, format="JPEG")
    return out.getvalue()


HINTS = [
    ("API key not valid", "The key is wrong or was copied with extra characters. Copy it again from aistudio.google.com/apikey."),
    ("API_KEY_INVALID", "The key is wrong or was copied with extra characters. Copy it again from aistudio.google.com/apikey."),
    ("HTTP 403", "The key isn't allowed to use this API or model (or the Generative Language API is off for its project)."),
    ("HTTP 404", "This model name isn't available for your key. Run with --list to see the ones that are."),
    ("HTTP 429", "Free-tier quota or rate limit reached. Wait a minute (or until tomorrow for the daily limit) and try again."),
    ("Timeout", "The model took too long. Check your internet connection, or try a lighter model: --model gemini-flash-lite-latest"),
    ("ConnectError", "Can't reach Google from this PC. Check the internet connection, VPN, proxy or firewall."),
    ("Connection", "Can't reach Google from this PC. Check the internet connection, VPN, proxy or firewall."),
    ("location is not supported", "Google doesn't offer this API in your region from this network."),
]


def _hint(message: str) -> str | None:
    return next((h for needle, h in HINTS if needle.lower() in message.lower()), None)


def _redact(text: str, secrets: list[str]) -> str:
    for s in secrets:
        if s:
            text = text.replace(s, "<key>")
    return text


async def _run(label: str, call, secrets: list[str]) -> bool:
    start = time.perf_counter()
    try:
        run = await call()
    except Exception as exc:  # report every failure, whatever its type
        print(f"  ✗ {label}: FAILED after {time.perf_counter() - start:.1f}s")
        message = _redact(describe_error(exc), secrets)
        print(f"      {message}")
        if hint := _hint(message):
            print(f"      → {hint}")
        return False
    out = run.output
    if hasattr(out, "items"):
        summary = f"is_food={out.is_food}, items={[i.name_en for i in out.items]}"
    else:
        summary = f"explained {len(out.dishes)} dish(es)"
    print(f"  ✓ {label}: OK in {time.perf_counter() - start:.1f}s ({run.model}) {summary}")
    return True


async def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m happygut_api.diagnose")
    parser.add_argument("photo", nargs="?", help="a food photo to test with (JPG, PNG or WebP)")
    parser.add_argument("--model", help="test only this model name instead of the configured ones")
    parser.add_argument("--list", action="store_true", help="list the models each key can use, then stop")
    args = parser.parse_args(argv)
    s = get_settings()
    secrets = [s.gemini_api_key, s.groq_api_key]

    print("Keys read from .env / environment:")
    for name, value in (("GEMINI_API_KEY", s.gemini_api_key), ("GROQ_API_KEY", s.groq_api_key)):
        print(f"  {name}: {'set (' + str(len(value)) + ' characters)' if value else 'NOT SET'}")
    if s.gemini_api_key and (s.gemini_api_key != s.gemini_api_key.strip() or s.gemini_api_key[0] in "'\""):
        print("  ! GEMINI_API_KEY has spaces or quotes around it: remove them in .env")

    catalog = model_catalog.fetch(s.gemini_api_key, s.groq_api_key, s.gemini_base_url or model_catalog.GEMINI_API)
    for error in catalog.errors:
        print(f"  ! {_redact(error, secrets)}")
    if args.list:
        for provider, names in (("Gemini", catalog.gemini), ("Groq", catalog.groq)):
            print(f"\n{provider} models this key can use:" if names is not None else f"\n{provider}: not listed")
            for name in sorted(names or []):
                print(f"  {name}")
        return 0

    if args.photo:
        try:
            image = sanitise(Path(args.photo).read_bytes(), s.max_image_bytes, s.max_image_side)
        except (OSError, ImageRejected) as exc:
            print(f"Can't use that photo: {exc}")
            return 2
        print(f"Photo: {args.photo} ({image.width}x{image.height} after resizing)")
    else:
        image = sanitise(_test_image(), s.max_image_bytes, s.max_image_side)
        print("Photo: a generated test drawing (pass a real photo path to test with it)")

    perception_prompt = load_prompt(s.prompts_dir, "meal-perception")
    explanation_prompt = load_prompt(s.prompts_dir, "meal-explanation")
    if args.model:
        perception_models = explanation_models = [args.model]
    else:
        choice = model_catalog.choose(s, catalog)
        print("\nModels the backend will use (configured names checked against what the keys can use):")
        print(f"  perception:  {' → '.join(choice.perception)}")
        print(f"  explanation: {' → '.join(choice.explanation)}")
        for note in choice.notes:
            if not note.startswith(("Gemini model list", "Groq model list")):
                print(f"  note: {note}")
        perception_models, explanation_models = choice.perception, choice.explanation

    ok = True
    for name in dict.fromkeys(perception_models):
        print(f"\nPerception model: {name}")
        try:
            model = build_model([name], s.gemini_api_key, s.groq_api_key, s.gemini_base_url)
        except RuntimeError as exc:
            print(f"  ✗ skipped: {exc}")
            ok = False
            continue
        agent = PydanticPerceiver(model, perception_prompt, s.model_timeout_s)
        ok &= await _run("text", lambda: agent.perceive(text="kacchi biryani and borhani", image=None, lang="en"), secrets)
        ok &= await _run("photo", lambda: agent.perceive(text=None, image=image, lang="en"), secrets)

    for name in dict.fromkeys(explanation_models):
        print(f"\nExplanation model: {name}")
        try:
            model = build_model([name], s.gemini_api_key, s.groq_api_key, s.gemini_base_url)
        except RuntimeError as exc:
            print(f"  ✗ skipped: {exc}")
            ok = False
            continue
        agent = PydanticExplainer(model, explanation_prompt, s.model_timeout_s)
        ok &= await _run("explanation", lambda: agent.explain(packet=PACKET, lang="en", diagnosis="CD"), secrets)

    print("\nAll model checks passed." if ok else "\nSome checks failed: send the lines marked ✗ (they contain no keys).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
