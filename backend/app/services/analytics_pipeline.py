"""
GrowthOS — Analytics Pipeline
===============================
Async ingestion + aggregation of engagement events from X API.
Produces analytics snapshots for the dashboard.

Architecture:
    X API Webhook/Poll → Event Ingestion (async) → Redis Buffer →
    Aggregation Worker (Celery) → PostgreSQL snapshots → Dashboard API
"""

from __future__ import annotations
import asyncio, logging, time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger("growthOS.analytics")


# --- Event Models ---
class EngagementType(str, Enum):
    LIKE = "like"
    RETWEET = "retweet"
    REPLY = "reply"
    QUOTE = "quote"
    BOOKMARK = "bookmark"
    IMPRESSION = "impression"
    PROFILE_VISIT = "profile_visit"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"

class EngagementEvent(BaseModel):
    event_id: str
    account_id: str
    tweet_id: str
    event_type: EngagementType
    actor_id: str | None = None     # who performed the action
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict)

class AnalyticsSnapshot(BaseModel):
    """Periodic analytics snapshot for an account."""
    account_id: str
    period_start: datetime
    period_end: datetime
    total_impressions: int = 0
    total_engagements: int = 0
    total_followers_gained: int = 0
    total_followers_lost: int = 0
    engagement_rate: float = 0.0
    top_tweet_id: str | None = None
    top_tweet_engagements: int = 0
    tweets_published: int = 0
    avg_likes_per_tweet: float = 0.0
    avg_retweets_per_tweet: float = 0.0
    avg_replies_per_tweet: float = 0.0
    engagement_by_hour: dict[int, int] = Field(default_factory=lambda: {h: 0 for h in range(24)})
    engagement_by_type: dict[str, int] = Field(default_factory=dict)
    best_performing_hour: int = 0

class TweetAnalytics(BaseModel):
    """Per-tweet analytics."""
    tweet_id: str
    account_id: str
    impressions: int = 0
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    quotes: int = 0
    bookmarks: int = 0
    engagement_rate: float = 0.0
    virality_score: float = 0.0  # from virality scorer
    first_hour_velocity: float = 0.0
    published_at: datetime | None = None


# --- Event Buffer (Redis-backed in production) ---
class EventBuffer:
    """
    In-memory buffer that simulates Redis LIST + ZADD patterns.
    Production: Use Redis LPUSH/BRPOP for event queue,
    ZADD for time-series, HSET for counters with TTL.

    Redis patterns used:
        - events:{account_id} → LIST of raw events (TTL: 48h)
        - counters:{account_id}:{tweet_id} → HASH {likes, rts, replies, ...}
        - hourly:{account_id}:{date} → ZSET of engagement counts by hour
        - snapshot:{account_id}:{date} → STRING (cached snapshot JSON, TTL: 24h)
    """

    def __init__(self):
        self._events: list[EngagementEvent] = []
        self._counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._hourly: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))

    async def push_event(self, event: EngagementEvent):
        """Buffer an incoming event. Production: LPUSH to Redis."""
        self._events.append(event)
        key = f"{event.account_id}:{event.tweet_id}"
        self._counters[key][event.event_type.value] += 1
        self._hourly[event.account_id][event.timestamp.hour] += 1
        logger.debug(f"Buffered event: {event.event_type.value} on {event.tweet_id}")

    async def flush(self, batch_size: int = 100) -> list[EngagementEvent]:
        """Drain up to batch_size events. Production: BRPOP from Redis."""
        batch = self._events[:batch_size]
        self._events = self._events[batch_size:]
        return batch

    def get_tweet_counters(self, account_id: str, tweet_id: str) -> dict[str, int]:
        return dict(self._counters.get(f"{account_id}:{tweet_id}", {}))

    def get_hourly_distribution(self, account_id: str) -> dict[int, int]:
        return dict(self._hourly.get(account_id, {}))


# --- Aggregation Engine ---
class AnalyticsAggregator:
    """Aggregates raw events into snapshots and per-tweet analytics."""

    def __init__(self, buffer: EventBuffer):
        self.buffer = buffer

    async def process_batch(self) -> int:
        """Process a batch of events from the buffer. Returns count processed."""
        events = await self.buffer.flush(batch_size=500)
        if not events:
            return 0

        # Group by account
        by_account: dict[str, list[EngagementEvent]] = defaultdict(list)
        for event in events:
            by_account[event.account_id].append(event)

        for account_id, account_events in by_account.items():
            await self._process_account_events(account_id, account_events)

        logger.info(f"Processed {len(events)} events across {len(by_account)} accounts")
        return len(events)

    async def _process_account_events(self, account_id: str, events: list[EngagementEvent]):
        """Process events for a single account."""
        # In production: UPDATE PostgreSQL counters, INSERT into time-series table
        by_tweet: dict[str, list[EngagementEvent]] = defaultdict(list)
        for event in events:
            by_tweet[event.tweet_id].append(event)

        for tweet_id, tweet_events in by_tweet.items():
            analytics = self._compute_tweet_analytics(account_id, tweet_id, tweet_events)
            # Production: UPSERT into tweet_analytics table
            logger.debug(f"Tweet {tweet_id}: {analytics.engagement_rate:.2%} ER, {analytics.impressions} imp")

    def _compute_tweet_analytics(self, account_id: str, tweet_id: str, events: list[EngagementEvent]) -> TweetAnalytics:
        counters = self.buffer.get_tweet_counters(account_id, tweet_id)
        likes = counters.get("like", 0)
        retweets = counters.get("retweet", 0)
        replies = counters.get("reply", 0)
        quotes = counters.get("quote", 0)
        bookmarks = counters.get("bookmark", 0)
        impressions = counters.get("impression", 0) or 1

        total_eng = likes + retweets + replies + quotes + bookmarks
        return TweetAnalytics(
            tweet_id=tweet_id, account_id=account_id,
            impressions=impressions, likes=likes, retweets=retweets,
            replies=replies, quotes=quotes, bookmarks=bookmarks,
            engagement_rate=total_eng / impressions)

    async def generate_snapshot(self, account_id: str, period_hours: int = 24) -> AnalyticsSnapshot:
        """Generate a snapshot for the dashboard."""
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(hours=period_hours)
        hourly = self.buffer.get_hourly_distribution(account_id)
        best_hour = max(hourly, key=hourly.get, default=14) if hourly else 14

        return AnalyticsSnapshot(
            account_id=account_id,
            period_start=period_start, period_end=now,
            engagement_by_hour={h: hourly.get(h, 0) for h in range(24)},
            best_performing_hour=best_hour)


# --- Ingestion Pipeline ---
class IngestionPipeline:
    """
    Async event ingestion from X API webhooks and polling.

    Two ingestion modes:
    1. Webhook (real-time): X sends events to our endpoint
    2. Polling (fallback): We fetch metrics every N minutes

    Both feed into the same EventBuffer → Aggregation pipeline.
    """

    def __init__(self):
        self.buffer = EventBuffer()
        self.aggregator = AnalyticsAggregator(self.buffer)
        self._running = False

    async def ingest_webhook_event(self, payload: dict) -> EngagementEvent:
        """Process a single webhook event from X API."""
        event = EngagementEvent(
            event_id=payload.get("id", f"evt_{int(time.time()*1000)}"),
            account_id=payload.get("account_id", ""),
            tweet_id=payload.get("tweet_id", ""),
            event_type=EngagementType(payload.get("event_type", "like")),
            actor_id=payload.get("actor_id"),
            metadata=payload.get("metadata", {}))
        await self.buffer.push_event(event)
        return event

    async def poll_tweet_metrics(self, account_id: str, tweet_ids: list[str]):
        """Poll X API for latest metrics on a list of tweets."""
        # Production: GET https://api.twitter.com/2/tweets?ids=...&tweet.fields=public_metrics
        for tweet_id in tweet_ids:
            # Simulate fetched metrics
            for event_type in [EngagementType.IMPRESSION, EngagementType.LIKE]:
                await self.buffer.push_event(EngagementEvent(
                    event_id=f"poll_{tweet_id}_{event_type.value}_{int(time.time())}",
                    account_id=account_id, tweet_id=tweet_id, event_type=event_type))

    async def run_aggregation_loop(self, interval_seconds: int = 60):
        """Continuous aggregation loop. In production: Celery Beat task."""
        self._running = True
        while self._running:
            processed = await self.aggregator.process_batch()
            if processed:
                logger.info(f"Aggregated {processed} events")
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self._running = False


if __name__ == "__main__":
    async def demo():
        pipeline = IngestionPipeline()
        # Simulate webhook events
        for i in range(20):
            await pipeline.ingest_webhook_event({
                "id": f"evt_{i}", "account_id": "acc_001",
                "tweet_id": f"tweet_{i % 3}", "event_type": "like",
                "actor_id": f"user_{i}"})
        for i in range(5):
            await pipeline.ingest_webhook_event({
                "id": f"rt_{i}", "account_id": "acc_001",
                "tweet_id": "tweet_0", "event_type": "retweet"})

        processed = await pipeline.aggregator.process_batch()
        print(f"Processed {processed} events")
        snapshot = await pipeline.aggregator.generate_snapshot("acc_001")
        print(f"Snapshot: {snapshot.engagement_by_hour}")

    asyncio.run(demo())
