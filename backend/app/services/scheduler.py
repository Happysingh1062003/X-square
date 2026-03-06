"""
GrowthOS — Smart Posting Scheduler
====================================
Celery-based smart scheduler with audience activity modeling,
timezone-aware optimal posting, and rate-limit-aware queue management.

Architecture:
    1. Audience Activity Model: Build histogram of follower activity by hour
    2. Optimal Slot Calculator: Merge audience model + content type priors
    3. Queue Manager: Distribute scheduled posts across optimal slots
    4. Rate Limiter: Enforce X API quotas (1500 tweets/month, 300 req/15min)
    5. Celery Worker: Execute posts at scheduled times with retry
"""

from __future__ import annotations
import logging, math, random
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("growthOS.scheduler")


# --- Rate Limit Tracking ---
class RateLimitConfig(BaseModel):
    monthly_tweet_limit: int = 1500        # X API free tier
    requests_per_15min: int = 300          # X API rate limit
    safety_margin: float = 0.9            # use only 90% of limits
    min_interval_seconds: int = 120       # minimum 2 min between posts

class RateLimitState(BaseModel):
    tweets_this_month: int = 0
    month_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0))
    requests_in_window: int = 0
    window_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_post_time: datetime | None = None

    def can_post(self, config: RateLimitConfig, now: datetime | None = None) -> tuple[bool, str]:
        now = now or datetime.now(timezone.utc)
        effective_monthly = int(config.monthly_tweet_limit * config.safety_margin)
        if self.tweets_this_month >= effective_monthly:
            remaining_days = (self.month_start.replace(month=self.month_start.month % 12 + 1) - now).days
            return False, f"Monthly limit reached ({self.tweets_this_month}/{config.monthly_tweet_limit}). Resets in {remaining_days} days."
        if (now - self.window_start).total_seconds() < 900:
            effective_window = int(config.requests_per_15min * config.safety_margin)
            if self.requests_in_window >= effective_window:
                wait = 900 - (now - self.window_start).total_seconds()
                return False, f"Rate limit: {self.requests_in_window}/{config.requests_per_15min} in window. Wait {wait:.0f}s."
        else:
            self.requests_in_window = 0
            self.window_start = now
        if self.last_post_time:
            elapsed = (now - self.last_post_time).total_seconds()
            if elapsed < config.min_interval_seconds:
                return False, f"Too soon. Wait {config.min_interval_seconds - elapsed:.0f}s."
        return True, "OK"

    def record_post(self, now: datetime | None = None):
        now = now or datetime.now(timezone.utc)
        self.tweets_this_month += 1
        self.requests_in_window += 1
        self.last_post_time = now


# --- Audience Activity Model ---
class AudienceActivityModel(BaseModel):
    """Histogram of follower activity by hour (0-23 UTC)."""
    account_id: str
    hourly_activity: list[float] = Field(default_factory=lambda: [0.0] * 24)
    timezone_distribution: dict[str, float] = Field(default_factory=dict)
    sample_size: int = 0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_engagement_data(cls, account_id: str, engagement_hours: list[int], sample_size: int) -> "AudienceActivityModel":
        """Build model from historical engagement timestamps."""
        histogram = [0.0] * 24
        for hour in engagement_hours:
            histogram[hour % 24] += 1
        total = sum(histogram) or 1
        histogram = [h / total for h in histogram]
        return cls(account_id=account_id, hourly_activity=histogram, sample_size=sample_size)

    @classmethod
    def default_model(cls, account_id: str) -> "AudienceActivityModel":
        """Default model for cold-start accounts (US tech audience prior)."""
        # Peak: 9-11 AM EST and 1-3 PM EST → 14-16 UTC and 18-20 UTC
        histogram = [0.01]*24
        for h in [13,14,15,16,17,18,19,20]: histogram[h] = 0.08
        for h in [12,21]: histogram[h] = 0.05
        total = sum(histogram)
        return cls(account_id=account_id, hourly_activity=[h/total for h in histogram], sample_size=0)


# --- Content Type Priors ---
CONTENT_TYPE_HOUR_BONUS = {
    "single_tweet": {9: 0.1, 10: 0.15, 14: 0.1, 15: 0.15, 16: 0.1},  # midday peaks
    "thread": {7: 0.15, 8: 0.2, 9: 0.15, 20: 0.1, 21: 0.1},  # morning/evening readers
    "reply": {},  # replies are time-sensitive, no prior
}


# --- Optimal Post Time Calculator ---
class PostSlot(BaseModel):
    hour_utc: int
    score: float
    label: str = ""  # "prime", "good", "acceptable"

class OptimalTimeCalculator:
    """Calculate best posting times by merging audience model + content type priors."""

    def __init__(self, audience_model: AudienceActivityModel):
        self.model = audience_model

    def get_optimal_slots(self, content_type: str = "single_tweet", num_slots: int = 5) -> list[PostSlot]:
        bonuses = CONTENT_TYPE_HOUR_BONUS.get(content_type, {})
        scores = []
        for hour in range(24):
            base = self.model.hourly_activity[hour]
            bonus = bonuses.get(hour, 0.0)
            combined = base + bonus
            scores.append((hour, combined))
        scores.sort(key=lambda x: x[1], reverse=True)
        slots = []
        for i, (hour, score) in enumerate(scores[:num_slots]):
            label = "prime" if i < 2 else ("good" if i < 4 else "acceptable")
            slots.append(PostSlot(hour_utc=hour, score=round(score, 4), label=label))
        return slots

    def get_next_optimal_time(self, content_type: str = "single_tweet", after: datetime | None = None) -> datetime:
        """Get the next optimal posting time after the given datetime."""
        after = after or datetime.now(timezone.utc)
        slots = self.get_optimal_slots(content_type, num_slots=3)
        best_hours = [s.hour_utc for s in slots]
        for day_offset in range(3):
            for hour in best_hours:
                candidate = after.replace(hour=hour, minute=random.randint(0, 15), second=0, microsecond=0) + timedelta(days=day_offset)
                if candidate > after + timedelta(minutes=30):
                    return candidate
        return after + timedelta(hours=1)


# --- Scheduled Post Models ---
class PostStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"

class ScheduledPost(BaseModel):
    id: str
    account_id: str
    content: str
    content_type: str = "single_tweet"
    thread_tweets: list[str] = Field(default_factory=list)
    scheduled_time: datetime | None = None
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: datetime | None = None
    tweet_id: str | None = None  # X API tweet ID after publishing
    retry_count: int = 0
    max_retries: int = 3
    error_message: str | None = None


# --- Queue Manager ---
class QueueManager:
    """Manages the posting queue with smart scheduling and rate limiting."""

    def __init__(self, rate_config: RateLimitConfig | None = None):
        self.rate_config = rate_config or RateLimitConfig()
        self.rate_state = RateLimitState()
        self.queue: list[ScheduledPost] = []

    def add_to_queue(self, post: ScheduledPost, audience_model: AudienceActivityModel | None = None) -> ScheduledPost:
        """Add a post to the queue, auto-scheduling if no time specified."""
        if post.scheduled_time is None and audience_model:
            calculator = OptimalTimeCalculator(audience_model)
            existing_times = [p.scheduled_time for p in self.queue if p.scheduled_time and p.status in (PostStatus.QUEUED, PostStatus.SCHEDULED)]
            proposed = calculator.get_next_optimal_time(post.content_type)
            # Avoid conflicts — ensure min 2-hour gap
            while any(abs((proposed - t).total_seconds()) < 7200 for t in existing_times if t):
                proposed += timedelta(hours=1)
            post.scheduled_time = proposed
        post.status = PostStatus.SCHEDULED
        self.queue.append(post)
        self.queue.sort(key=lambda p: p.scheduled_time or datetime.max.replace(tzinfo=timezone.utc))
        logger.info(f"Post {post.id} scheduled for {post.scheduled_time}")
        return post

    def get_due_posts(self, now: datetime | None = None) -> list[ScheduledPost]:
        now = now or datetime.now(timezone.utc)
        return [p for p in self.queue if p.status == PostStatus.SCHEDULED and p.scheduled_time and p.scheduled_time <= now]

    def get_remaining_quota(self) -> dict:
        used = self.rate_state.tweets_this_month
        limit = self.rate_config.monthly_tweet_limit
        return {"used": used, "limit": limit, "remaining": limit - used, "utilization_pct": round(used / limit * 100, 1)}


# --- Celery Task Definitions ---
# In production, these would be actual Celery tasks
# from celery import Celery
# celery_app = Celery('growthOS', broker='redis://localhost:6379/0')

async def publish_tweet(post: ScheduledPost, rate_state: RateLimitState, rate_config: RateLimitConfig) -> ScheduledPost:
    """
    Publish a scheduled tweet to X via API.
    Celery task with retry logic and rate limit awareness.
    """
    can_post, reason = rate_state.can_post(rate_config)
    if not can_post:
        logger.warning(f"Cannot post {post.id}: {reason}")
        if post.retry_count < post.max_retries:
            post.retry_count += 1
            post.scheduled_time = datetime.now(timezone.utc) + timedelta(minutes=15)
            post.status = PostStatus.SCHEDULED
            return post
        post.status = PostStatus.FAILED
        post.error_message = reason
        return post

    post.status = PostStatus.PUBLISHING
    try:
        # Production X API call:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://api.twitter.com/2/tweets",
        #         headers={"Authorization": f"Bearer {oauth_token}"},
        #         json={"text": post.content})
        #     data = response.json()
        #     post.tweet_id = data["data"]["id"]

        logger.info(f"Published post {post.id}: {post.content[:50]}...")
        post.status = PostStatus.PUBLISHED
        post.published_at = datetime.now(timezone.utc)
        post.tweet_id = f"mock_{post.id}"
        rate_state.record_post()

    except Exception as e:
        logger.error(f"Failed to publish {post.id}: {e}")
        if post.retry_count < post.max_retries:
            post.retry_count += 1
            delay = min(60 * (2 ** post.retry_count), 3600)
            post.scheduled_time = datetime.now(timezone.utc) + timedelta(seconds=delay)
            post.status = PostStatus.SCHEDULED
            post.error_message = str(e)
        else:
            post.status = PostStatus.FAILED
            post.error_message = f"Failed after {post.max_retries} retries: {e}"

    return post


# --- Scheduler Loop (Celery Beat equivalent) ---
async def scheduler_tick(queue_manager: QueueManager):
    """Run once per minute by Celery Beat to process due posts."""
    due_posts = queue_manager.get_due_posts()
    logger.info(f"Scheduler tick: {len(due_posts)} posts due")
    for post in due_posts:
        result = await publish_tweet(post, queue_manager.rate_state, queue_manager.rate_config)
        logger.info(f"Post {result.id}: {result.status.value}")


if __name__ == "__main__":
    import asyncio

    model = AudienceActivityModel.default_model("account_001")
    calc = OptimalTimeCalculator(model)
    slots = calc.get_optimal_slots("single_tweet")
    print("Optimal posting slots:")
    for s in slots:
        print(f"  {s.hour_utc}:00 UTC — score: {s.score} ({s.label})")

    qm = QueueManager()
    post = ScheduledPost(id="post_001", account_id="acc_001", content="Test tweet from GrowthOS 🚀")
    scheduled = qm.add_to_queue(post, model)
    print(f"\nScheduled for: {scheduled.scheduled_time}")
    print(f"Quota: {qm.get_remaining_quota()}")
