"""Two-pass visual design research over retained vintage sold-listing evidence.

The evidence metadata is only for retrieval. The research model receives the actual
cached image bytes and both passes are persisted with their complete provenance.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Any

from app.config import Settings
from app.domain.errors import StudioError

DEFAULT_ROOT = Path("/home/ubuntu/shirtfaced-research/vintage-ebay-images")
RUNS_DIR = "research-runs"
PASS_1_VERSION = "vintage-research-pass1-v1"
PASS_2_VERSION = "vintage-research-pass2-v1"
DEFAULT_IMAGE_LIMIT = 16
MAX_IMAGE_LIMIT = 24

PASS_1_PROMPT = """You are a print on demand design research expert. Based on these photos of best selling designs, generate 10 design ideas and prompts for an image generator to create similar designs for the retro skate, surf and streetwear niche. Make all of the designs original, but base these on trends and best selling elements from the screenshots of current best sellers using trendy color palettes, design elements, font styles, and popular themes specifically for the retro streetwear niche.
Make the 10 prompts extremely detailed and specific for the skate, surf and streetwear niche and for an image generator like Chat GPT 2.0 in Kittl design to create graphic designs for t-shirts all using design trends featured in these screenshots.
Include \"flat graphic design, no background, transparent PNG, print on demand ready\" to every prompt.

Return exactly 10 concepts. Do not copy logos, slogans, characters, brand identifiers, or an evidence artwork's exact composition. Synthesize recurring visual tendencies across the supplied evidence. Keep concept_number fixed from 1 through 10."""

PASS_2_PROMPT = """Make these 10 t-shirt design prompts more detailed but still based on the best selling trends featured in the screenshots.

Return exactly the same 10 concepts in the same order and with the same concept_number, title and idea. Expand only the generation prompt substantially: add composition, typography, hierarchy, illustration treatment, print texture, palette, ink/colour behaviour, linework, negative space, placement and production-specific detail wherever the evidence supports those tendencies. Every prompt must still end with or include \"flat graphic design, no background, transparent PNG, print on demand ready\". Do not copy logos, slogans, characters, brand identifiers, or an evidence artwork's exact composition."""

CONCEPT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["concepts"],
    "properties": {
        "concepts": {
            "type": "array",
            "minItems": 10,
            "maxItems": 10,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["concept_number", "title", "idea", "prompt"],
                "properties": {
                    "concept_number": {"type": "integer", "minimum": 1, "maximum": 10},
                    "title": {"type": "string", "minLength": 1},
                    "idea": {"type": "string", "minLength": 1},
                    "prompt": {"type": "string", "minLength": 80},
                },
            },
        }
    },
}


class VintageResearchError(StudioError):
    """The evidence set or research model returned something unusable."""


def root() -> Path:
    return Path(os.environ.get("VINTAGE_EVIDENCE_ROOT", str(DEFAULT_ROOT))).resolve()


def _runs_root() -> Path:
    path = root() / RUNS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def evidence_records() -> list[dict[str, Any]]:
    """Return evidence rows with image URLs and enough metadata for UI filtering."""
    evidence_root = root()
    if not evidence_root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for child in evidence_root.iterdir():
        if not child.is_dir() or not child.name.isdigit():
            continue
        record = _read_json(child / "record.json", {})
        if not record:
            continue
        images = sorted(
            p.name
            for p in child.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        )
        if not images:
            continue
        listing_id = str(record.get("listing_id") or child.name)
        rows.append(
            {
                **record,
                "listing_id": listing_id,
                "images": [f"/vintage-evidence/image/{listing_id}/{name}" for name in images],
            }
        )
    rows.sort(key=lambda row: str(row.get("listing_id", "")), reverse=True)
    return rows


def filter_evidence(filters: dict[str, Any]) -> list[dict[str, Any]]:
    rows = evidence_records()
    query = str(filters.get("query") or "").strip().lower()
    brand = str(filters.get("brand") or "").strip().lower()
    era = str(filters.get("era") or "").strip().lower()
    tradition = str(filters.get("tradition") or "").strip().lower()

    def matches(row: dict[str, Any]) -> bool:
        hay = " ".join(
            str(value or "")
            for value in (
                row.get("brand"),
                row.get("title"),
                row.get("era_claim"),
                row.get("tradition"),
                " ".join(row.get("graphic_tags") or []),
            )
        ).lower()
        return (
            (not query or query in hay)
            and (not brand or str(row.get("brand") or "").lower() == brand)
            and (not era or str(row.get("era_claim") or "").lower() == era)
            and (
                not tradition
                or str(row.get("tradition") or "").lower() == tradition
            )
        )

    return [row for row in rows if matches(row)]


def _image_path(image_url: str) -> tuple[str, Path]:
    prefix = "/vintage-evidence/image/"
    if not image_url.startswith(prefix):
        raise VintageResearchError(f"Not a vintage evidence image: {image_url}")
    rest = image_url[len(prefix) :]
    parts = rest.split("/", 1)
    if len(parts) != 2 or not parts[0].isdigit() or Path(parts[1]).name != parts[1]:
        raise VintageResearchError(f"Invalid evidence image path: {image_url}")
    listing_id, filename = parts
    listing_dir = (root() / listing_id).resolve()
    evidence_root = root()
    if evidence_root not in listing_dir.parents:
        raise VintageResearchError("Evidence path escaped the evidence root")
    path = (listing_dir / filename).resolve()
    if path.parent != listing_dir or not path.is_file():
        raise VintageResearchError(f"Evidence image is missing: {image_url}")
    return listing_id, path


def select_images(
    *,
    filters: dict[str, Any],
    listing_ids: list[str] | None,
    image_urls: list[str] | None,
    image_limit: int = DEFAULT_IMAGE_LIMIT,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Resolve the exact listing records and exact image files supplied to the model."""
    image_limit = max(1, min(image_limit, MAX_IMAGE_LIMIT))
    rows = filter_evidence(filters)
    wanted = {str(item) for item in (listing_ids or []) if str(item).isdigit()}
    if wanted:
        rows = [row for row in rows if str(row.get("listing_id")) in wanted]

    by_url: dict[str, dict[str, Any]] = {}
    for row in rows:
        for url in row.get("images") or []:
            by_url[url] = row

    chosen_urls: list[str]
    if image_urls:
        chosen_urls = [url for url in image_urls if url in by_url][:image_limit]
    else:
        chosen_urls = []
        # Breadth first: first image from each listing before taking second images.
        depth = 0
        while len(chosen_urls) < image_limit:
            added = False
            for row in rows:
                images = row.get("images") or []
                if depth < len(images):
                    chosen_urls.append(images[depth])
                    added = True
                    if len(chosen_urls) >= image_limit:
                        break
            if not added:
                break
            depth += 1

    if not chosen_urls:
        raise VintageResearchError("No evidence images matched the selection.")

    images: list[dict[str, Any]] = []
    listing_map: dict[str, dict[str, Any]] = {}
    for url in chosen_urls:
        listing_id, path = _image_path(url)
        row = by_url[url]
        listing_map[listing_id] = {
            "listing_id": listing_id,
            "brand": row.get("brand"),
            "title": row.get("title"),
            "era_claim": row.get("era_claim"),
            "tradition": row.get("tradition"),
            "source_url": row.get("source_url"),
        }
        data = path.read_bytes()
        images.append(
            {
                "listing_id": listing_id,
                "image_url": url,
                "filename": path.name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "mime_type": mimetypes.guess_type(path.name)[0] or "image/jpeg",
                "byte_size": len(data),
                "path": path,
            }
        )
    return list(listing_map.values()), images


def _image_content(images: list[dict[str, Any]]) -> list[dict[str, str]]:
    content: list[dict[str, str]] = []
    for image in images:
        encoded = base64.b64encode(image["path"].read_bytes()).decode()
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:{image['mime_type']};base64,{encoded}",
            }
        )
    return content


def _call_model(client: Any, model: str, timeout: float, prompt: str, images: list[dict[str, Any]], *, prior: dict[str, Any] | None = None) -> tuple[dict[str, Any], str | None]:
    text = prompt
    if prior is not None:
        text += "\n\nPASS 1 OUTPUT TO EXPAND, WITHOUT CHANGING THE CONCEPTS:\n" + json.dumps(prior, ensure_ascii=False)
    try:
        response = client.responses.create(
            model=model,
            timeout=timeout,
            input=[
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": text}, *_image_content(images)],
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "vintage_design_research",
                    "strict": True,
                    "schema": CONCEPT_SCHEMA,
                }
            },
        )
    except Exception as error:
        raise VintageResearchError(f"Vintage research model request failed: {error}") from error
    raw = getattr(response, "output_text", "")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise VintageResearchError("Vintage research model did not return valid JSON.") from error
    _validate_concepts(parsed)
    return parsed, getattr(response, "id", None)


def _validate_concepts(payload: dict[str, Any]) -> None:
    concepts = payload.get("concepts")
    if not isinstance(concepts, list) or len(concepts) != 10:
        raise VintageResearchError("Research pass must return exactly 10 concepts.")
    numbers = [item.get("concept_number") for item in concepts if isinstance(item, dict)]
    if numbers != list(range(1, 11)):
        raise VintageResearchError("Research concepts must be numbered 1 through 10 in order.")
    suffix = "flat graphic design, no background, transparent PNG, print on demand ready"
    for item in concepts:
        if suffix.lower() not in str(item.get("prompt") or "").lower():
            raise VintageResearchError(
                f"Concept {item.get('concept_number')} is missing the required POD-ready phrase."
            )


def _validate_pass2(pass1: dict[str, Any], pass2: dict[str, Any]) -> None:
    _validate_concepts(pass2)
    for first, second in zip(pass1["concepts"], pass2["concepts"], strict=True):
        if first["concept_number"] != second["concept_number"]:
            raise VintageResearchError("Pass 2 changed concept numbering.")
        if first["title"].strip() != second["title"].strip():
            raise VintageResearchError(
                f"Pass 2 changed the title of concept {first['concept_number']}."
            )
        if first["idea"].strip() != second["idea"].strip():
            raise VintageResearchError(
                f"Pass 2 changed the idea of concept {first['concept_number']}."
            )
        first_prompt = first["prompt"].strip()
        second_prompt = second["prompt"].strip()
        minimum = max(len(first_prompt) + 120, int(len(first_prompt) * 1.2))
        if len(second_prompt) < minimum:
            raise VintageResearchError(
                f"Pass 2 did not substantially expand concept {first['concept_number']}."
            )


def _serialisable_image(image: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in image.items() if key != "path"}


def save_run(run: dict[str, Any]) -> dict[str, Any]:
    path = _runs_root() / f"{run['id']}.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)
    return run


def load_run(run_id: str) -> dict[str, Any]:
    try:
        uuid.UUID(run_id)
    except ValueError as error:
        raise VintageResearchError("Invalid research run id.") from error
    path = _runs_root() / f"{run_id}.json"
    run = _read_json(path, None)
    if not isinstance(run, dict):
        raise VintageResearchError("Research run not found.")
    return run


def list_runs() -> list[dict[str, Any]]:
    runs = []
    for path in sorted(_runs_root().glob("*.json"), reverse=True):
        run = _read_json(path, None)
        if isinstance(run, dict):
            runs.append(run)
    return runs


def execute_research(
    settings: Settings,
    *,
    filters: dict[str, Any],
    listing_ids: list[str] | None,
    image_urls: list[str] | None,
    image_limit: int = DEFAULT_IMAGE_LIMIT,
    model: str = "",
) -> dict[str, Any]:
    """Run both visual research passes and persist the complete provenance."""
    selected_model = model.strip() or settings.openai_review_model or settings.openai_text_model
    if not settings.openai_api_key or not selected_model:
        raise VintageResearchError(
            "OPENAI_API_KEY and OPENAI_REVIEW_MODEL or OPENAI_TEXT_MODEL must be configured."
        )
    listings, images = select_images(
        filters=filters,
        listing_ids=listing_ids,
        image_urls=image_urls,
        image_limit=image_limit,
    )

    from openai import OpenAI

    client = OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=settings.openai_timeout_seconds,
    )
    started = dt.datetime.now(dt.UTC)
    pass1, pass1_request_id = _call_model(
        client, selected_model, settings.openai_timeout_seconds, PASS_1_PROMPT, images
    )
    pass2, pass2_request_id = _call_model(
        client,
        selected_model,
        settings.openai_timeout_seconds,
        PASS_2_PROMPT,
        images,
        prior=pass1,
    )
    _validate_pass2(pass1, pass2)
    completed = dt.datetime.now(dt.UTC)

    run_id = str(uuid.uuid4())
    concepts = []
    for first, second in zip(pass1["concepts"], pass2["concepts"], strict=True):
        concepts.append(
            {
                "concept_number": first["concept_number"],
                "title": first["title"],
                "idea": first["idea"],
                "pass1_prompt": first["prompt"],
                "pass2_prompt": second["prompt"],
                "edited_prompt": None,
                "status": "pending",
                "review_note": "",
                "pipeline": None,
            }
        )

    return save_run(
        {
            "id": run_id,
            "status": "completed",
            "created_at": started.isoformat(),
            "completed_at": completed.isoformat(),
            "evidence_filters": filters,
            "evidence_listing_ids": [item["listing_id"] for item in listings],
            "evidence_listings": listings,
            "evidence_images": [_serialisable_image(image) for image in images],
            "pass1": {
                "prompt": PASS_1_PROMPT,
                "version": PASS_1_VERSION,
                "output": pass1,
                "provider_request_id": pass1_request_id,
            },
            "pass2": {
                "prompt": PASS_2_PROMPT,
                "version": PASS_2_VERSION,
                "output": pass2,
                "provider_request_id": pass2_request_id,
            },
            "model": selected_model,
            "model_settings": {"timeout_seconds": settings.openai_timeout_seconds},
            "concepts": concepts,
        }
    )


def update_concept(
    run_id: str,
    concept_number: int,
    *,
    status: str | None = None,
    edited_prompt: str | None = None,
    review_note: str | None = None,
) -> dict[str, Any]:
    run = load_run(run_id)
    concept = next(
        (item for item in run.get("concepts", []) if item.get("concept_number") == concept_number),
        None,
    )
    if concept is None:
        raise VintageResearchError("Research concept not found.")
    if status is not None:
        if status not in {"pending", "approved", "rejected"}:
            raise VintageResearchError("Status must be pending, approved or rejected.")
        concept["status"] = status
    if edited_prompt is not None:
        edited = edited_prompt.strip()
        if not edited:
            raise VintageResearchError("Edited prompt cannot be empty.")
        concept["edited_prompt"] = edited
    if review_note is not None:
        concept["review_note"] = review_note.strip()
    concept["updated_at"] = dt.datetime.now(dt.UTC).isoformat()
    save_run(run)
    return concept


def mark_pipeline(run_id: str, concept_number: int, payload: dict[str, Any]) -> None:
    run = load_run(run_id)
    concept = next(
        (item for item in run.get("concepts", []) if item.get("concept_number") == concept_number),
        None,
    )
    if concept is None:
        raise VintageResearchError("Research concept not found.")
    concept["pipeline"] = payload
    concept["updated_at"] = dt.datetime.now(dt.UTC).isoformat()
    save_run(run)
