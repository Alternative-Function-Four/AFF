from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from constants import QUIET_HOUR_END, QUIET_HOUR_START, SG_TZ
from models import (
    ActiveDays,
    BudgetMode,
    EventRecord,
    FeedbackSignal,
    InMemoryStore,
    InteractionRecord,
    PreferenceProfile,
    PreferredTime,
    TimeWindow,
)


def make_request_id() -> str:
    return f"req_{uuid4().hex[:12]}"


def as_sg_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=SG_TZ)
    return value.astimezone(SG_TZ)


def now_sg(store: InMemoryStore) -> datetime:
    return as_sg_datetime(store.now_provider())


def make_ingestion_metrics() -> dict[str, Any]:
    return {
        "normalization_low_confidence_total": 0,
        "dedup_merge_action_total": {
            "skip": 0,
            "merge_sources": 0,
            "create_new": 0,
        },
        "source_parse_failures_total": 0,
    }


def append_ingestion_log(
    store: InMemoryStore,
    *,
    run_id: str,
    level: str,
    message: str,
    payload: dict[str, Any],
    user_id: str | None = None,
    source_id: str | None = None,
    event_id: str | None = None,
) -> None:
    store.ingestion_logs.append(
        {
            "timestamp": now_sg(store).isoformat(),
            "level": level,
            "service": "ingestion",
            "run_id": run_id,
            "user_id": user_id,
            "source_id": source_id,
            "event_id": event_id,
            "message": message,
            "payload": payload,
        }
    )


def default_preference_profile(user_id: str, now: datetime) -> PreferenceProfile:
    return PreferenceProfile(
        user_id=UUID(user_id),
        preferred_categories=["events", "food", "nightlife"],
        preferred_subcategories=[],
        budget_mode=BudgetMode.moderate,
        preferred_distance_km=8,
        active_days=ActiveDays.both,
        preferred_times=[PreferredTime.evening],
        anti_preferences=[],
        updated_at=now,
    )


def event_matches_window(event: EventRecord, time_window: TimeWindow, now: datetime) -> bool:
    start = event.occurrences[0].datetime_start.astimezone(SG_TZ)
    if time_window == TimeWindow.today:
        return start.date() == now.date()
    if time_window == TimeWindow.tonight:
        return start.date() == now.date() and start.hour >= 18
    if time_window == TimeWindow.weekend:
        return start.weekday() in {5, 6} and start <= now + timedelta(days=7)
    if time_window == TimeWindow.next_7_days:
        return now <= start <= now + timedelta(days=7)
    return True


def build_feed_score(
    user_id: str,
    event: EventRecord,
    profile: PreferenceProfile,
    budget: BudgetMode,
    interactions: list[InteractionRecord],
) -> tuple[float, list[str]]:
    score = 0.5
    reasons: list[str] = []

    if event.category in profile.preferred_categories:
        score += 0.25
        reasons.append(f"Matches preferred category '{event.category}'")

    if event.subcategory and event.subcategory in profile.preferred_subcategories:
        score += 0.1
        reasons.append(f"Matches subcategory '{event.subcategory}'")

    lowered = f"{event.title} {event.category}".lower()
    if any(term.lower() in lowered for term in profile.anti_preferences):
        score -= 0.2
        reasons.append("Contains anti-preference signal")

    budget_limits = {
        BudgetMode.budget: 30,
        BudgetMode.moderate: 80,
        BudgetMode.premium: 200,
        BudgetMode.any: None,
    }
    limit = budget_limits[budget]
    if limit is not None and event.price and event.price.max is not None and event.price.max > limit:
        score -= 0.15

    for item in interactions:
        if item.user_id != user_id or item.event_id != event.event_id:
            continue
        if item.signal == FeedbackSignal.interested.value:
            score += 0.3
            reasons.append("Boosted by interested feedback")
        elif item.signal == FeedbackSignal.not_for_me.value:
            score -= 0.45
            reasons.append("Lowered by not_for_me feedback")
        elif item.signal == FeedbackSignal.already_knew.value:
            score -= 0.1
            reasons.append("Novelty reduced by already_knew feedback")

    score = round(max(0.0, min(score, 1.5)), 4)
    if not reasons:
        reasons.append("General relevance baseline")
    return score, reasons


def is_quiet_hours(moment: datetime) -> bool:
    hour = moment.hour
    return hour >= QUIET_HOUR_START or hour < QUIET_HOUR_END


def notifications_count_today(store: InMemoryStore, user_id: str, now: datetime) -> int:
    total = 0
    for uid, log in store.notification_logs:
        if uid != user_id:
            continue
        if log.created_at.astimezone(SG_TZ).date() != now.date():
            continue
        if log.status.value in {"queued", "sent"}:
            total += 1
    return total


def build_similar_events(store: InMemoryStore, candidate_event: dict[str, Any]) -> list[dict[str, Any]]:
    title = str(candidate_event.get("title") or "").lower()
    candidate_start = candidate_event.get("datetime_start")
    similar_events: list[dict[str, Any]] = []

    for event in store.events.values():
        similarity = 0.35
        event_title = event.title.lower()
        if title and any(token in event_title for token in title.split()):
            similarity += 0.35
        if title and event_title in title:
            similarity += 0.25

        try:
            start_a = datetime.fromisoformat(str(candidate_start)).astimezone(SG_TZ)
            start_b = event.occurrences[0].datetime_start.astimezone(SG_TZ)
            hours_delta = abs((start_a - start_b).total_seconds()) / 3600
            if hours_delta <= 2:
                similarity += 0.2
            elif hours_delta <= 12:
                similarity += 0.1
        except ValueError:
            pass

        similar_events.append(
            {
                "event_id": event.event_id,
                "title": event.title,
                "datetime_start": event.occurrences[0].datetime_start.isoformat(),
                "venue_name": event.venue_name,
                "similarity_score": round(min(similarity, 0.99), 3),
            }
        )

    similar_events.sort(key=lambda item: item["similarity_score"], reverse=True)
    return similar_events[:5]
