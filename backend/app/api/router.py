"""
GrowthOS — FastAPI Router for Tweet Generation
================================================
RESTful API endpoint /api/v1/generate/tweet with full request/response models,
JWT auth, rate limiting, and async LLM pipeline integration.
"""

from __future__ import annotations
import time, logging, os
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.tweet_generator import (
    TweetGenerator, GeneratorConfig, GenerateTweetRequest, GenerateTweetResponse,
    ContentType, TweetStyle, TweetVariant, ThreadTweet,
)

logger = logging.getLogger("growthOS.api.generate")

router = APIRouter(prefix="/api/v1", tags=["content-generation"])


# --- Auth Dependencies ---
class CurrentUser(BaseModel):
    user_id: str
    account_id: str
    plan: str = "free"  # free, pro, agency
    monthly_generations_remaining: int = 100

async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> CurrentUser:
    """
    JWT validation. Production: decode JWT, verify signature, extract claims.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    # Production: jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    # Mock for development:
    return CurrentUser(user_id="user_001", account_id="acc_001", plan="pro", monthly_generations_remaining=500)


# --- Rate Limiting ---
class RateLimiter:
    """Per-user rate limiter using sliding window."""
    def __init__(self):
        self._windows: dict[str, list[float]] = {}

    def check(self, user_id: str, max_requests: int = 30, window_seconds: int = 60) -> bool:
        now = time.time()
        if user_id not in self._windows:
            self._windows[user_id] = []
        # Clean old entries
        self._windows[user_id] = [t for t in self._windows[user_id] if now - t < window_seconds]
        if len(self._windows[user_id]) >= max_requests:
            return False
        self._windows[user_id].append(now)
        return True

rate_limiter = RateLimiter()


# --- Request/Response Models (API layer) ---
class GenerateRequestAPI(BaseModel):
    """API-level request model with validation."""
    topic: str = Field(..., min_length=3, max_length=500, description="Topic to generate content about")
    content_type: ContentType = Field(default=ContentType.SINGLE_TWEET, description="Type of content to generate")
    style: TweetStyle = Field(default=TweetStyle.AUTHORITATIVE, description="Writing style")
    niche: str = Field(default="general", max_length=100, description="Content niche (AI, SaaS, finance, etc.)")
    target_audience: str = Field(default="tech professionals", max_length=200)
    num_variants: int = Field(default=3, ge=1, le=10, description="Number of variants to generate")
    thread_length: int = Field(default=5, ge=3, le=15, description="Thread length (only for threads)")
    include_cta: bool = Field(default=True, description="Include call-to-action")
    reference_tweets: list[str] = Field(default_factory=list, max_length=5, description="High-performing tweet examples")
    original_tweet_text: str | None = Field(default=None, description="Required for reply generation")
    reply_intent: str | None = Field(default=None, description="Reply intent: agree, disagree, add_value, question")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Why most AI startups fail in their first year",
                "content_type": "single_tweet",
                "style": "provocative",
                "niche": "AI",
                "target_audience": "startup founders",
                "num_variants": 3,
                "include_cta": True,
            }
        }

class GenerateResponseAPI(BaseModel):
    """API response wrapper."""
    success: bool = True
    request_id: str
    content_type: ContentType
    variants: list[TweetVariant] = Field(default_factory=list)
    thread: list[ThreadTweet] = Field(default_factory=list)
    generation_time_ms: float
    model_used: str
    credits_remaining: int
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: str
    detail: str | None = None


# --- Endpoints ---

@router.post(
    "/generate/tweet",
    response_model=GenerateResponseAPI,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Generation failed"},
    },
    summary="Generate AI-powered tweet/thread/reply content",
    description=(
        "Generates high-quality tweet variants, threads, or replies using AI. "
        "Content is personalized based on account history and audience data. "
        "Supports multiple styles and hook types."
    ),
)
async def generate_tweet(
    request: GenerateRequestAPI,
    user: CurrentUser = Depends(get_current_user),
):
    # Rate limiting
    if not rate_limiter.check(user.user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 30 requests per minute.",
        )

    # Quota check
    if user.monthly_generations_remaining <= 0:
        raise HTTPException(
            status_code=429,
            detail="Monthly generation quota exhausted. Upgrade your plan.",
        )

    # Validate content-type specific requirements
    if request.content_type == ContentType.REPLY and not request.original_tweet_text:
        raise HTTPException(status_code=400, detail="original_tweet_text is required for reply generation")

    # Build internal request
    gen_request = GenerateTweetRequest(
        topic=request.topic,
        content_type=request.content_type,
        style=request.style,
        niche=request.niche,
        target_audience=request.target_audience,
        num_variants=request.num_variants,
        thread_length=request.thread_length,
        include_cta=request.include_cta,
        reference_tweets=request.reference_tweets,
        original_tweet_text=request.original_tweet_text,
        reply_intent=request.reply_intent,
        # In production: load from user's account profile
        author_voice_description=None,
        top_performing_hooks=[],
    )

    try:
        generator = TweetGenerator(GeneratorConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
        ))
        result = await generator.generate(gen_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Generation failed for user {user.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Content generation failed. Please try again.")

    return GenerateResponseAPI(
        request_id=result.request_id,
        content_type=result.content_type,
        variants=result.variants,
        thread=result.thread,
        generation_time_ms=result.generation_time_ms,
        model_used=result.model_used,
        credits_remaining=user.monthly_generations_remaining - 1,
    )


@router.get("/generate/quota", summary="Check remaining generation quota")
async def get_quota(user: CurrentUser = Depends(get_current_user)):
    return {
        "user_id": user.user_id,
        "plan": user.plan,
        "monthly_generations_remaining": user.monthly_generations_remaining,
        "daily_limit": 50 if user.plan == "free" else 500,
    }


# --- App Factory ---
def create_app():
    """Create the FastAPI app with all routers."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="GrowthOS API",
        version="1.0.0",
        description="AI-powered Twitter/X growth platform API",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://growthOS.app"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app

if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
