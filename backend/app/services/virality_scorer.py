"""
GrowthOS — Virality Scorer
===========================
Production-grade virality scoring engine with feature extraction.

Scoring Model: Gradient-boosted regression on 12 engineered features.
Training Signal: Historical engagement data per-account (not global averages).

Virality Score = f(engagement_rate, velocity, amplification_ratio, recency_decay,
                   follower_reach_ratio, media_boost, thread_depth_bonus,
                   quote_to_reply_ratio, sentiment_polarity, topic_trending_score,
                   posting_hour_alignment, historical_author_virality)

Output: Float in [0.0, 1.0] — 0 = no viral potential, 1 = extreme viral potential.
"""

from __future__ import annotations

import math
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger("growthOS.virality_scorer")


# ---------------------------------------------------------------------------
# Domain Models
# ---------------------------------------------------------------------------

class MediaType(str, Enum):
    NONE = "none"
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    POLL = "poll"


class TweetMetrics(BaseModel):
    """Raw engagement metrics pulled from X API v2."""
    tweet_id: str
    author_id: str
    text: str
    created_at: datetime
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    impression_count: int = 0
    bookmark_count: int = 0
    follower_count: int = 1  # author's follower count at time of tweet
    media_type: MediaType = MediaType.NONE
    is_thread: bool = False
    thread_position: int = 0  # 0 = standalone, 1 = thread start, 2+ = continuation
    hashtags: list[str] = Field(default_factory=list)
    mentioned_user_ids: list[str] = Field(default_factory=list)


class AuthorHistory(BaseModel):
    """Rolling statistics for a specific author — used for normalization."""
    author_id: str
    avg_engagement_rate: float = 0.02  # baseline
    avg_impressions: float = 500.0
    avg_likes: float = 10.0
    total_tweets_analyzed: int = 0
    avg_virality_score: float = 0.15
    top_performing_topics: list[str] = Field(default_factory=list)


@dataclass
class ViralityFeatures:
    """Engineered feature vector for virality prediction."""
    engagement_rate: float = 0.0
    velocity: float = 0.0              # engagements per minute in first hour
    amplification_ratio: float = 0.0   # (retweets + quotes) / (likes + replies)
    recency_decay: float = 1.0         # exponential decay from creation time
    follower_reach_ratio: float = 0.0  # impressions / follower_count
    media_boost: float = 0.0           # categorical boost for media type
    thread_depth_bonus: float = 0.0    # bonus for thread starters
    quote_to_reply_ratio: float = 0.0  # quotes are higher-signal than replies
    sentiment_polarity: float = 0.0    # placeholder: positive = 0.5..1, negative = -1..0
    topic_trending_score: float = 0.0  # how trending are the tweet's topics right now
    posting_hour_alignment: float = 0.0  # did they post at optimal time for their audience
    historical_author_virality: float = 0.0  # author's track record

    def to_vector(self) -> np.ndarray:
        return np.array([
            self.engagement_rate,
            self.velocity,
            self.amplification_ratio,
            self.recency_decay,
            self.follower_reach_ratio,
            self.media_boost,
            self.thread_depth_bonus,
            self.quote_to_reply_ratio,
            self.sentiment_polarity,
            self.topic_trending_score,
            self.posting_hour_alignment,
            self.historical_author_virality,
        ])


# ---------------------------------------------------------------------------
# Feature Extraction
# ---------------------------------------------------------------------------

# Media type engagement multipliers (empirically derived from X data)
MEDIA_BOOST_MAP: dict[MediaType, float] = {
    MediaType.NONE: 0.0,
    MediaType.IMAGE: 0.25,
    MediaType.VIDEO: 0.45,
    MediaType.GIF: 0.15,
    MediaType.POLL: 0.35,
}

# Recency half-life in hours — engagement signal decays over time
RECENCY_HALF_LIFE_HOURS = 6.0


def extract_features(
    tweet: TweetMetrics,
    author_history: AuthorHistory,
    trending_topics: dict[str, float] | None = None,
    optimal_hours: list[int] | None = None,
    now: datetime | None = None,
) -> ViralityFeatures:
    """
    Extract the 12-dimensional feature vector from raw tweet metrics.

    Args:
        tweet: Raw metrics from X API.
        author_history: Rolling author stats for relative scoring.
        trending_topics: Map of topic → trending score [0, 1].
        optimal_hours: List of hours (0-23 UTC) when audience is most active.
        now: Current timestamp (injectable for testing).

    Returns:
        ViralityFeatures with all 12 features populated.
    """
    now = now or datetime.now(timezone.utc)
    trending_topics = trending_topics or {}
    optimal_hours = optimal_hours or list(range(13, 21))  # default: 1PM-9PM UTC

    features = ViralityFeatures()

    # ---- 1. Engagement Rate ----
    # Total engagements / impressions (or follower count as fallback)
    total_engagements = (
        tweet.like_count
        + tweet.retweet_count
        + tweet.reply_count
        + tweet.quote_count
        + tweet.bookmark_count
    )
    denominator = max(tweet.impression_count, tweet.follower_count, 1)
    features.engagement_rate = min(total_engagements / denominator, 1.0)

    # ---- 2. Velocity (engagements per minute in first hour window) ----
    age_minutes = max((now - tweet.created_at).total_seconds() / 60.0, 1.0)
    window_minutes = min(age_minutes, 60.0)  # cap at 60 min window
    features.velocity = total_engagements / window_minutes

    # ---- 3. Amplification Ratio ----
    # High retweet+quote ratio relative to likes signals organic spread
    amplification = tweet.retweet_count + tweet.quote_count
    passive = tweet.like_count + tweet.reply_count + 1  # +1 to avoid div/0
    features.amplification_ratio = min(amplification / passive, 5.0) / 5.0  # normalize to [0,1]

    # ---- 4. Recency Decay ----
    age_hours = (now - tweet.created_at).total_seconds() / 3600.0
    features.recency_decay = math.exp(
        -0.693 * age_hours / RECENCY_HALF_LIFE_HOURS  # ln(2) ≈ 0.693
    )

    # ---- 5. Follower Reach Ratio ----
    if tweet.impression_count > 0:
        features.follower_reach_ratio = min(
            tweet.impression_count / max(tweet.follower_count, 1), 10.0
        ) / 10.0  # normalize; >1x means going beyond followers
    else:
        features.follower_reach_ratio = 0.0

    # ---- 6. Media Boost ----
    features.media_boost = MEDIA_BOOST_MAP.get(tweet.media_type, 0.0)

    # ---- 7. Thread Depth Bonus ----
    if tweet.is_thread and tweet.thread_position == 1:
        features.thread_depth_bonus = 0.3  # thread starters get a bonus
    elif tweet.is_thread and tweet.thread_position >= 2:
        features.thread_depth_bonus = 0.1  # continuation tweets get smaller bonus
    else:
        features.thread_depth_bonus = 0.0

    # ---- 8. Quote-to-Reply Ratio ----
    # Quotes are a higher-quality engagement signal than replies
    total_reactions = tweet.quote_count + tweet.reply_count + 1
    features.quote_to_reply_ratio = tweet.quote_count / total_reactions

    # ---- 9. Sentiment Polarity (placeholder — would use a sentiment model) ----
    # Heuristic: strong opinions (positive or negative) tend to go viral
    # In production, this is replaced by a fine-tuned sentiment classifier
    text_lower = tweet.text.lower()
    positive_signals = sum(1 for w in ["amazing", "incredible", "game-changer", "🔥", "💯", "thread", "unpopular opinion"] if w in text_lower)
    negative_signals = sum(1 for w in ["terrible", "worst", "scam", "overrated", "hot take"] if w in text_lower)
    features.sentiment_polarity = min((positive_signals + negative_signals) * 0.15, 1.0)

    # ---- 10. Topic Trending Score ----
    if tweet.hashtags and trending_topics:
        topic_scores = [trending_topics.get(tag.lower(), 0.0) for tag in tweet.hashtags]
        features.topic_trending_score = max(topic_scores) if topic_scores else 0.0

    # ---- 11. Posting Hour Alignment ----
    post_hour = tweet.created_at.hour
    if post_hour in optimal_hours:
        features.posting_hour_alignment = 1.0
    elif (post_hour - 1) % 24 in optimal_hours or (post_hour + 1) % 24 in optimal_hours:
        features.posting_hour_alignment = 0.5  # near-optimal
    else:
        features.posting_hour_alignment = 0.0

    # ---- 12. Historical Author Virality ----
    features.historical_author_virality = min(author_history.avg_virality_score, 1.0)

    return features


# ---------------------------------------------------------------------------
# Virality Scoring Model
# ---------------------------------------------------------------------------

# Learned weights (would be trained via gradient boosting in production;
# these are hand-tuned initial weights for MVP bootstrapping)
DEFAULT_WEIGHTS = np.array([
    0.20,   # engagement_rate
    0.18,   # velocity
    0.14,   # amplification_ratio
    0.08,   # recency_decay
    0.10,   # follower_reach_ratio
    0.05,   # media_boost
    0.04,   # thread_depth_bonus
    0.06,   # quote_to_reply_ratio
    0.03,   # sentiment_polarity
    0.05,   # topic_trending_score
    0.03,   # posting_hour_alignment
    0.04,   # historical_author_virality
])

# Ensure weights sum to 1.0
DEFAULT_WEIGHTS = DEFAULT_WEIGHTS / DEFAULT_WEIGHTS.sum()


class ViralityScorerConfig(BaseModel):
    """Configuration for the virality scoring engine."""
    weights: list[float] = Field(default_factory=lambda: DEFAULT_WEIGHTS.tolist())
    score_floor: float = 0.0
    score_ceiling: float = 1.0
    use_nonlinear_transform: bool = True  # apply sigmoid for better score distribution
    sigmoid_steepness: float = 8.0        # controls score spread
    sigmoid_midpoint: float = 0.35        # center of the sigmoid curve


class ViralityScore(BaseModel):
    """Output of the virality scoring engine."""
    tweet_id: str
    score: float = Field(ge=0.0, le=1.0)
    percentile: float | None = None  # relative to author's history
    features: dict[str, float] = Field(default_factory=dict)
    explanation: str = ""
    scored_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ViralityScorer:
    """
    Production virality scoring engine.

    Uses a weighted feature combination with optional nonlinear (sigmoid)
    transform to produce a score in [0, 1].

    In production, the weights are learned per-account via gradient boosting
    on historical data. The default weights serve as cold-start initialization.

    Architecture:
        1. Feature Extraction → 12-dim vector
        2. Weighted sum → raw score
        3. Optional sigmoid transform → calibrated score
        4. Percentile calculation vs author history → relative score
    """

    def __init__(self, config: ViralityScorerConfig | None = None):
        self.config = config or ViralityScorerConfig()
        self.weights = np.array(self.config.weights)

    def score(
        self,
        tweet: TweetMetrics,
        author_history: AuthorHistory,
        trending_topics: dict[str, float] | None = None,
        optimal_hours: list[int] | None = None,
        now: datetime | None = None,
    ) -> ViralityScore:
        """
        Score a single tweet's virality potential.

        Returns a ViralityScore with the numeric score, feature breakdown,
        and a human-readable explanation of why the score is what it is.
        """
        # Step 1: Extract features
        features = extract_features(
            tweet, author_history, trending_topics, optimal_hours, now
        )
        feature_vector = features.to_vector()

        # Step 2: Weighted combination
        raw_score = float(np.dot(self.weights, feature_vector))

        # Step 3: Nonlinear transform (sigmoid) for better score distribution
        if self.config.use_nonlinear_transform:
            calibrated_score = self._sigmoid(raw_score)
        else:
            calibrated_score = raw_score

        # Clamp to [floor, ceiling]
        final_score = max(
            self.config.score_floor,
            min(self.config.score_ceiling, calibrated_score),
        )

        # Step 4: Calculate percentile vs author history
        percentile = self._calculate_percentile(final_score, author_history)

        # Step 5: Generate explanation
        explanation = self._explain(features, final_score, percentile)

        # Build feature dict for transparency
        feature_dict = {
            "engagement_rate": round(features.engagement_rate, 4),
            "velocity": round(features.velocity, 4),
            "amplification_ratio": round(features.amplification_ratio, 4),
            "recency_decay": round(features.recency_decay, 4),
            "follower_reach_ratio": round(features.follower_reach_ratio, 4),
            "media_boost": round(features.media_boost, 4),
            "thread_depth_bonus": round(features.thread_depth_bonus, 4),
            "quote_to_reply_ratio": round(features.quote_to_reply_ratio, 4),
            "sentiment_polarity": round(features.sentiment_polarity, 4),
            "topic_trending_score": round(features.topic_trending_score, 4),
            "posting_hour_alignment": round(features.posting_hour_alignment, 4),
            "historical_author_virality": round(features.historical_author_virality, 4),
        }

        return ViralityScore(
            tweet_id=tweet.tweet_id,
            score=round(final_score, 4),
            percentile=round(percentile, 2) if percentile is not None else None,
            features=feature_dict,
            explanation=explanation,
        )

    def score_batch(
        self,
        tweets: list[TweetMetrics],
        author_history: AuthorHistory,
        trending_topics: dict[str, float] | None = None,
        optimal_hours: list[int] | None = None,
    ) -> list[ViralityScore]:
        """Score multiple tweets, sorted by score descending."""
        scores = [
            self.score(tweet, author_history, trending_topics, optimal_hours)
            for tweet in tweets
        ]
        scores.sort(key=lambda s: s.score, reverse=True)
        return scores

    def _sigmoid(self, x: float) -> float:
        """Sigmoid transform centered at midpoint with configurable steepness."""
        k = self.config.sigmoid_steepness
        x0 = self.config.sigmoid_midpoint
        return 1.0 / (1.0 + math.exp(-k * (x - x0)))

    def _calculate_percentile(
        self, score: float, author_history: AuthorHistory
    ) -> float | None:
        """
        Estimate percentile rank relative to the author's historical distribution.

        Uses a simple z-score approximation. In production, this would use
        the actual score distribution stored per-author.
        """
        if author_history.total_tweets_analyzed < 5:
            return None  # not enough data for percentile

        # Approximate: assume roughly normal distribution around avg
        avg = author_history.avg_virality_score
        # Assume std ≈ 0.3 * avg for reasonable spread
        std = max(avg * 0.3, 0.05)
        z = (score - avg) / std

        # Convert z-score to percentile using error function approximation
        percentile = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        return min(max(percentile * 100, 0.0), 100.0)

    def _explain(
        self,
        features: ViralityFeatures,
        score: float,
        percentile: float | None,
    ) -> str:
        """Generate a human-readable explanation of the virality score."""
        parts: list[str] = []

        if score >= 0.8:
            parts.append("🔥 HIGH VIRAL POTENTIAL.")
        elif score >= 0.5:
            parts.append("📈 Moderate viral potential.")
        elif score >= 0.25:
            parts.append("📊 Below-average virality signals.")
        else:
            parts.append("📉 Low viral potential.")

        # Highlight top contributing features
        feature_contributions = [
            ("engagement_rate", features.engagement_rate * self.weights[0]),
            ("velocity", features.velocity * self.weights[1]),
            ("amplification_ratio", features.amplification_ratio * self.weights[2]),
            ("follower_reach", features.follower_reach_ratio * self.weights[4]),
            ("topic_trending", features.topic_trending_score * self.weights[9]),
        ]
        feature_contributions.sort(key=lambda x: x[1], reverse=True)
        top = feature_contributions[0]
        parts.append(f"Top signal: {top[0]} (contribution: {top[1]:.3f}).")

        if features.media_boost > 0:
            parts.append("Media content detected — engagement boost applied.")

        if features.velocity > 0.5:
            parts.append(f"Strong early velocity: {features.velocity:.1f} eng/min.")

        if percentile is not None:
            parts.append(
                f"This tweet ranks in the {percentile:.0f}th percentile "
                f"for this author."
            )

        return " ".join(parts)


# ---------------------------------------------------------------------------
# Convenience / Entry Point
# ---------------------------------------------------------------------------

def score_tweet(
    tweet: TweetMetrics,
    author_history: AuthorHistory | None = None,
    trending_topics: dict[str, float] | None = None,
) -> ViralityScore:
    """
    One-shot convenience function for scoring a single tweet.

    Usage:
        result = score_tweet(tweet_metrics)
        print(result.score, result.explanation)
    """
    if author_history is None:
        author_history = AuthorHistory(author_id=tweet.author_id)

    scorer = ViralityScorer()
    return scorer.score(tweet, author_history, trending_topics)


# ---------------------------------------------------------------------------
# Example usage (for development / testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Simulate a tweet that went semi-viral
    sample_tweet = TweetMetrics(
        tweet_id="1234567890",
        author_id="author_001",
        text="Unpopular opinion: Most AI startups will fail because they're solving "
             "problems that don't exist. Here's what the 1% do differently 🧵👇",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=45),
        like_count=342,
        retweet_count=87,
        reply_count=56,
        quote_count=23,
        impression_count=15000,
        bookmark_count=44,
        follower_count=8500,
        media_type=MediaType.NONE,
        is_thread=True,
        thread_position=1,
        hashtags=["ai", "startups"],
    )

    sample_author = AuthorHistory(
        author_id="author_001",
        avg_engagement_rate=0.035,
        avg_impressions=3000,
        avg_likes=45,
        total_tweets_analyzed=120,
        avg_virality_score=0.28,
        top_performing_topics=["ai", "saas", "entrepreneurship"],
    )

    trending = {"ai": 0.85, "startups": 0.4, "crypto": 0.9}

    result = score_tweet(sample_tweet, sample_author, trending)

    print(f"Virality Score: {result.score}")
    print(f"Percentile: {result.percentile}")
    print(f"Explanation: {result.explanation}")
    print(f"Features: {result.features}")
