from __future__ import annotations

from datetime import datetime, timedelta
import re
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

SG_TZ = ZoneInfo("Asia/Singapore")


def _meta(agent: str, run_id: str | None) -> dict[str, str]:
    return {
        "agent": agent,
        "version": "v1",
        "run_id": run_id or str(uuid4()),
    }


def ok_envelope(agent: str, data: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    return {
        "status": "ok",
        "data": data,
        "meta": _meta(agent=agent, run_id=run_id),
    }


def error_envelope(
    agent: str,
    code: str,
    message: str,
    retryable: bool,
    details: dict[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "details": details or {},
        },
        "meta": _meta(agent=agent, run_id=run_id),
    }


def _parse_datetime(raw_value: str | None, now: datetime) -> tuple[datetime, str | None, float]:
    if raw_value is None or not raw_value.strip():
        fallback = now.replace(hour=20, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return fallback, "Missing date schedule; defaulted to next evening.", 0.45

    text = raw_value.strip()
    try:
        value = datetime.fromisoformat(text)
        return value.astimezone(SG_TZ), None, 0.0
    except ValueError:
        pass

    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%d %b %Y %H:%M",
        "%d %b %Y %I:%M%p",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=SG_TZ), None, 0.05
        except ValueError:
            continue

    lowered = text.lower()
    if "tonight" in lowered:
        tonight = now.replace(hour=20, minute=0, second=0, microsecond=0)
        if tonight < now:
            tonight += timedelta(days=1)
        return tonight, "Interpreted vague schedule as tonight 20:00.", 0.25

    fallback = now.replace(hour=20, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return fallback, f"Unable to parse schedule '{text}', used fallback.", 0.4


def _infer_category(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["jazz", "concert", "gig", "music"]):
        return "concert"
    if any(token in lowered for token in ["food", "hawker", "dinner", "brunch"]):
        return "food_experience"
    if any(token in lowered for token in ["comedy", "club", "night", "bar"]):
        return "nightlife"
    if any(token in lowered for token in ["film", "movie", "cinema"]):
        return "film"
    return "other"


def _parse_price(raw_price: str | None) -> tuple[float | None, float | None]:
    if not raw_price:
        return None, None
    numbers = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", raw_price)]
    if not numbers:
        return None, None
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return min(numbers), max(numbers)


def normalize_event_agent(payload: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    agent = "EventNormalizerAgent"
    if "raw_event" not in payload or not isinstance(payload["raw_event"], dict):
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="Missing raw_event object",
            retryable=False,
            details={"required": ["raw_event", "city_context"]},
            run_id=run_id,
        )

    raw = payload["raw_event"]
    city_context = str(payload.get("city_context", "Singapore"))
    now = datetime.now(SG_TZ)

    title = (raw.get("raw_title") or "").strip()
    if not title:
        title = "Untitled activity"

    datetime_start, date_note, date_penalty = _parse_datetime(raw.get("raw_date_or_schedule"), now)

    description = raw.get("raw_description")
    location = (raw.get("raw_location") or "").strip() or None
    source_url = raw.get("raw_url")
    price_min, price_max = _parse_price(raw.get("raw_price"))

    confidence = 0.95
    parsing_notes: list[str] = []

    if raw.get("raw_title") in (None, ""):
        confidence -= 0.35
        parsing_notes.append("Missing title; used placeholder title.")
    if date_note:
        confidence -= date_penalty
        parsing_notes.append(date_note)
    if not location:
        confidence -= 0.12
        parsing_notes.append("Missing location value.")
    if not source_url:
        confidence -= 0.08
        parsing_notes.append("Missing source URL.")

    confidence = round(max(0.0, min(confidence, 1.0)), 3)
    parsing_note_text = " | ".join(parsing_notes) if parsing_notes else None

    normalized_event = {
        "title": title,
        "category": _infer_category(f"{title} {description or ''}"),
        "subcategory": None,
        "datetime_start": datetime_start.isoformat(),
        "datetime_end": (datetime_start + timedelta(hours=2)).isoformat(),
        "is_recurring": False,
        "recurrence_rule": None,
        "venue_name": location,
        "venue_address": location,
        "venue_lat": 1.29 if city_context.lower() == "singapore" else None,
        "venue_lng": 103.85 if city_context.lower() == "singapore" else None,
        "price_min": price_min,
        "price_max": price_max,
        "currency": "SGD" if (price_min is not None or price_max is not None) else None,
        "description": description,
        "tags": [],
        "source_url": source_url,
        "confidence_score": confidence,
        "parsing_notes": parsing_note_text,
    }

    return ok_envelope(agent=agent, data={"normalized_event": normalized_event}, run_id=run_id)


def deduplicate_event_agent(payload: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    agent = "DeduplicationAgent"
    candidate_event = payload.get("candidate_event")
    similar_events = payload.get("similar_events")

    if not isinstance(candidate_event, dict) or not isinstance(similar_events, list):
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="candidate_event and similar_events are required",
            retryable=False,
            details={"required": ["candidate_event", "similar_events"]},
            run_id=run_id,
        )

    if not similar_events:
        decision = {
            "is_duplicate": False,
            "duplicate_of_id": None,
            "merge_action": "create_new",
            "confidence": 0.82,
            "reasoning": "No sufficiently similar existing events.",
            "requires_manual_review": False,
        }
        return ok_envelope(agent=agent, data=decision, run_id=run_id)

    best = max(similar_events, key=lambda item: float(item.get("similarity_score", 0.0)))
    similarity = round(float(best.get("similarity_score", 0.0)), 3)

    if similarity >= 0.92:
        merge_action = "skip"
        is_duplicate = True
        confidence = similarity
        reasoning = "Near-identical event fingerprint detected."
    elif similarity >= 0.75:
        merge_action = "merge_sources"
        is_duplicate = True
        confidence = round(similarity - 0.03, 3)
        reasoning = "Substantial overlap with existing event; merge provenance."
    else:
        merge_action = "create_new"
        is_duplicate = False
        confidence = round(max(0.52, similarity + 0.05), 3)
        reasoning = "Similarity is weak; create a new canonical event."

    requires_manual_review = confidence < 0.65
    decision = {
        "is_duplicate": is_duplicate,
        "duplicate_of_id": best.get("event_id") if is_duplicate else None,
        "merge_action": merge_action,
        "confidence": confidence,
        "reasoning": reasoning,
        "requires_manual_review": requires_manual_review,
    }
    return ok_envelope(agent=agent, data=decision, run_id=run_id)


def source_hunter_agent(payload: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    agent = "SourceHunterAgent"
    city = payload.get("city")
    categories = payload.get("categories")
    if not isinstance(city, str) or not isinstance(categories, list):
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="city and categories are required",
            retryable=False,
            details={"required": ["city", "categories"]},
            run_id=run_id,
        )

    sources = []
    for category in categories:
        slug = str(category).replace("_", "-")
        sources.append(
            {
                "name": f"{city} {category} source",
                "url": f"https://{slug}.example.sg/feed",
                "source_type": "local_blog",
                "access_method": "rss",
                "update_frequency_estimate": "daily",
                "reliability_score": 70,
                "policy_risk_score": 20,
            }
        )

    return ok_envelope(agent=agent, data={"sources": sources}, run_id=run_id)


def ingestion_agent(payload: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    agent = "IngestionAgent"
    raw_events = payload.get("raw_events")
    if not isinstance(raw_events, list):
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="raw_events list is required",
            retryable=False,
            details={"required": ["raw_events"]},
            run_id=run_id,
        )

    processed = len(raw_events)
    parseable = sum(1 for event in raw_events if bool(event.get("raw_title")))
    return ok_envelope(
        agent=agent,
        data={
            "processed_count": processed,
            "parseable_count": parseable,
            "failed_count": processed - parseable,
        },
        run_id=run_id,
    )


def recommendation_agent(payload: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    agent = "RecommendationAgent"
    candidate_events = payload.get("candidate_events")
    profile = payload.get("profile")
    if not isinstance(candidate_events, list):
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="candidate_events list is required",
            retryable=False,
            details={"required": ["candidate_events"]},
            run_id=run_id,
        )
    if not isinstance(profile, dict):
        return error_envelope(
            agent=agent,
            code="PROFILE_NOT_FOUND",
            message="profile is required",
            retryable=True,
            details={},
            run_id=run_id,
        )

    preferred_categories = set(profile.get("preferred_categories", []))
    ranked = []
    for event in candidate_events:
        event_id = event.get("event_id")
        category = event.get("category")
        score = 0.6 + (0.3 if category in preferred_categories else 0.0)
        ranked.append(
            {
                "event_id": event_id,
                "relevance_score": round(min(score, 0.98), 3),
                "personal_pitch": "Matched to your profile",
                "reasons": [f"category:{category}"],
                "notify_immediately": score > 0.85,
                "notify_reason": "high_relevance" if score > 0.85 else "normal",
            }
        )
    ranked.sort(key=lambda item: item["relevance_score"], reverse=True)
    return ok_envelope(agent=agent, data={"ranked": ranked}, run_id=run_id)


def notification_composer_agent(payload: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    agent = "NotificationComposerAgent"
    event = payload.get("event")
    reason = payload.get("notify_reason")
    if not isinstance(event, dict) or not isinstance(reason, str):
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="event and notify_reason are required",
            retryable=False,
            details={"required": ["event", "notify_reason"]},
            run_id=run_id,
        )

    event_id = event.get("event_id", "")
    title = str(event.get("title", "AFF Alert"))[:100]
    body = str(reason)[:200]
    return ok_envelope(
        agent=agent,
        data={
            "title": title,
            "body": body,
            "deep_link": f"aff://events/{event_id}",
            "priority": "high",
        },
        run_id=run_id,
    )


def preference_profiler_agent(payload: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    agent = "PreferenceProfilerAgent"
    explicit = payload.get("explicit_preferences")
    history = payload.get("interaction_history", [])
    if not isinstance(explicit, dict) or not isinstance(history, list):
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="explicit_preferences and interaction_history are required",
            retryable=False,
            details={"required": ["explicit_preferences", "interaction_history"]},
            run_id=run_id,
        )

    categories = list(explicit.get("categories", []))
    boosts: dict[str, int] = {}
    penalties: dict[str, int] = {}
    for item in history:
        category = str(item.get("category", "other"))
        signal = item.get("signal")
        if signal == "interested":
            boosts[category] = boosts.get(category, 0) + 1
        if signal == "not_for_me":
            penalties[category] = penalties.get(category, 0) + 1

    ranked_categories = sorted(
        categories,
        key=lambda category: boosts.get(category, 0) - penalties.get(category, 0),
        reverse=True,
    )
    profile = {
        "preferred_categories": ranked_categories or categories,
        "preferred_subcategories": [],
        "price_sensitivity": explicit.get("budget_mode", "moderate"),
        "preferred_distance_km": 8,
        "active_days": "both",
        "preferred_times": list(explicit.get("time_preferences", ["evening"])),
        "taste_descriptors": ["adaptive profile"],
        "anti_preferences": [cat for cat, value in penalties.items() if value > 0],
    }
    return ok_envelope(agent=agent, data={"profile": profile}, run_id=run_id)
