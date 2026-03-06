"""
GrowthOS — AI Tweet & Thread Generator
========================================
Production LLM pipeline with retry logic, structured output parsing,
hook variants, and closed-loop prompt engineering.

LLM Selection Rationale:
    - Tweet generation: GPT-4o-mini (fast, cheap, great for short-form)
    - Thread generation: GPT-4o (coherence for long-form)
    - Reply generation: GPT-4o-mini (latency-sensitive)
    - Embeddings: text-embedding-3-small (cost-effective, 1536-dim)
"""

from __future__ import annotations
import asyncio, json, logging, re, time
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger("growthOS.tweet_generator")


# --- Configuration ---
class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class GeneratorConfig(BaseModel):
    provider: LLMProvider = LLMProvider.OPENAI
    tweet_model: str = "gpt-4o-mini"
    thread_model: str = "gpt-4o"
    reply_model: str = "gpt-4o-mini"
    max_retries: int = 3
    base_retry_delay: float = 1.0
    max_retry_delay: float = 30.0
    temperature: float = 0.8
    max_tokens_tweet: int = 500
    max_tokens_thread: int = 3000
    max_tokens_reply: int = 300
    api_key: str = ""


# --- Request / Response Models ---
class TweetStyle(str, Enum):
    AUTHORITATIVE = "authoritative"
    CONVERSATIONAL = "conversational"
    PROVOCATIVE = "provocative"
    EDUCATIONAL = "educational"
    STORYTELLING = "storytelling"

class ContentType(str, Enum):
    SINGLE_TWEET = "single_tweet"
    THREAD = "thread"
    REPLY = "reply"

class GenerateTweetRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    content_type: ContentType = ContentType.SINGLE_TWEET
    style: TweetStyle = TweetStyle.AUTHORITATIVE
    niche: str = "general"
    target_audience: str = "tech professionals"
    num_variants: int = Field(default=3, ge=1, le=10)
    thread_length: int = Field(default=5, ge=3, le=15)
    include_hooks: bool = True
    include_cta: bool = True
    reference_tweets: list[str] = Field(default_factory=list)
    tone_keywords: list[str] = Field(default_factory=list)
    avoid_keywords: list[str] = Field(default_factory=list)
    original_tweet_text: str | None = None
    reply_intent: str | None = None
    author_voice_description: str | None = None
    top_performing_hooks: list[str] = Field(default_factory=list)
    avg_engagement_rate: float | None = None

class TweetVariant(BaseModel):
    text: str
    hook_type: str = ""
    char_count: int = 0
    estimated_engagement: str = ""
    reasoning: str = ""

class ThreadTweet(BaseModel):
    position: int
    text: str
    purpose: str = ""

class GenerateTweetResponse(BaseModel):
    request_id: str = ""
    content_type: ContentType
    variants: list[TweetVariant] = Field(default_factory=list)
    thread: list[ThreadTweet] = Field(default_factory=list)
    generation_time_ms: float = 0.0
    model_used: str = ""
    tokens_used: int = 0


# --- Production Prompts ---
HOOK_GENERATOR_PROMPT = """You are an expert X (Twitter) growth strategist.
Generate {num_variants} tweet variants about: {topic}
NICHE: {niche} | AUDIENCE: {target_audience} | STYLE: {style}
{voice_section}
{reference_section}

HOOK TYPES (use {num_variants} different ones):
- "question" — Provocative question challenging assumptions
- "statistic" — Surprising number or data point
- "contrarian" — "Unpopular opinion:" challenging conventional wisdom
- "story" — "I [did X]..." micro-narrative
- "list_tease" — "X things I learned about Y"
- "bold_claim" — Strong declarative statement
- "analogy" — Unexpected comparison

RULES: Under 280 chars. Strategic line breaks. {cta_instruction}. No hashtag spam.

OUTPUT (JSON only, no fences):
{{"variants": [{{"text": "...", "hook_type": "...", "estimated_engagement": "high|medium|low", "reasoning": "..."}}]}}"""

THREAD_GENERATOR_PROMPT = """You are a master X thread writer.
Write a {thread_length}-tweet thread about: {topic}
NICHE: {niche} | AUDIENCE: {target_audience} | STYLE: {style}
{voice_section}

STRUCTURE:
- Tweet 1 (HOOK): Stop the scroll. End with "🧵👇"
- Tweets 2-{middle_end} (BODY): ONE idea per tweet. Concrete examples.
- Tweet {thread_length} (CTA): Key takeaway + ask for engagement.

RULES: Each under 280 chars. Use "1/" numbering. Include data/examples.

OUTPUT (JSON only):
{{"thread": [{{"position": 1, "text": "...", "purpose": "hook|context|insight|proof|cta"}}]}}"""

REPLY_GENERATOR_PROMPT = """You are an expert at high-value X replies that earn followers.
Write {num_variants} replies to: "{original_tweet}"
INTENT: {reply_intent} | NICHE: {niche} | STYLE: {style}
{voice_section}

STRATEGY: Add unique value. Make readers click your profile.
RULES: Under 280 chars. Never start with "Great point!". Never be sycophantic.

OUTPUT (JSON only):
{{"variants": [{{"text": "...", "hook_type": "add_value", "estimated_engagement": "...", "reasoning": "..."}}]}}"""


# --- LLM Client with Retry ---
class LLMClientError(Exception):
    pass

async def call_llm(
    prompt: str, model: str, config: GeneratorConfig,
    max_tokens: int = 500, system_prompt: str | None = None,
) -> tuple[str, int]:
    """Call LLM with exponential backoff retry. Returns (response, tokens)."""
    last_error = None
    for attempt in range(config.max_retries):
        try:
            # Production: use openai.AsyncOpenAI client
            # response = await client.chat.completions.create(
            #     model=model, messages=[...], temperature=config.temperature,
            #     max_tokens=max_tokens, response_format={"type": "json_object"})
            # return response.choices[0].message.content, response.usage.total_tokens

            logger.info(f"LLM call attempt {attempt+1}/{config.max_retries} → {model}")
            await asyncio.sleep(0.1)
            return _mock_response(prompt), 150
        except Exception as e:
            last_error = e
            delay = min(config.base_retry_delay * (2 ** attempt), config.max_retry_delay)
            if "429" in str(e): delay = max(delay, 10.0)
            logger.warning(f"LLM fail (attempt {attempt+1}): {e}. Retry in {delay:.1f}s")
            await asyncio.sleep(delay)
    raise LLMClientError(f"Failed after {config.max_retries} attempts: {last_error}")

def _mock_response(prompt: str) -> str:
    if "thread" in prompt.lower():
        return json.dumps({"thread": [
            {"position": 1, "text": "I spent 6 months studying the top 1% of SaaS founders.\n\nThey all do ONE thing differently.\n\n🧵👇", "purpose": "hook"},
            {"position": 2, "text": "2/ They don't build features.\nThey build systems that make features obsolete.", "purpose": "insight"},
            {"position": 3, "text": "3/ Instead of 10 notification features, they built a preference engine.\n\nResult: 40% fewer support tickets.", "purpose": "proof"},
            {"position": 4, "text": "4/ Stop thinking in features.\nStart thinking in systems.\n\nBookmark this. Follow for more.", "purpose": "cta"},
        ]})
    return json.dumps({"variants": [
        {"text": "Most AI startups will fail.\n\nNot because the tech is bad.\nBut because they're solving problems that don't exist.", "hook_type": "contrarian", "estimated_engagement": "high", "reasoning": "Contrarian take with clear structure"},
        {"text": "What if 90% of AI products could be replaced by a spreadsheet?\n\nThe best AI companies know this.\nThat's why they focus on the 10% that can't.", "hook_type": "question", "estimated_engagement": "high", "reasoning": "Provocative question"},
    ]})


# --- Output Parsing ---
def parse_llm_output(raw: str, content_type: ContentType) -> dict:
    """Parse LLM JSON output with 4-stage fallback."""
    for strategy in [
        lambda r: json.loads(r),
        lambda r: json.loads(re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', r, re.DOTALL).group(1)),
        lambda r: json.loads(re.sub(r',\s*([}\]])', r'\1', r.strip())),
        lambda r: json.loads(r[r.find('{'):r.rfind('}')+1]),
    ]:
        try: return strategy(raw)
        except: continue
    raise ValueError(f"Failed to parse LLM output: {raw[:200]}")


# --- Prompt Assembly ---
def build_prompt(request: GenerateTweetRequest) -> str:
    voice = f"YOUR VOICE: {request.author_voice_description}" if request.author_voice_description else ""
    if request.top_performing_hooks:
        voice += "\nTOP HOOKS: " + " | ".join(request.top_performing_hooks[:3])
    refs = "\nREFERENCE TWEETS:\n" + "\n".join(f"- {t}" for t in request.reference_tweets[:3]) if request.reference_tweets else ""
    cta = "End with subtle CTA" if request.include_cta else "No CTA"

    if request.content_type == ContentType.THREAD:
        return THREAD_GENERATOR_PROMPT.format(
            thread_length=request.thread_length, topic=request.topic, niche=request.niche,
            target_audience=request.target_audience, style=request.style.value,
            voice_section=voice, middle_end=request.thread_length - 1)
    elif request.content_type == ContentType.REPLY:
        return REPLY_GENERATOR_PROMPT.format(
            num_variants=request.num_variants, original_tweet=request.original_tweet_text or "",
            reply_intent=request.reply_intent or "add_value", niche=request.niche,
            style=request.style.value, voice_section=voice)
    else:
        return HOOK_GENERATOR_PROMPT.format(
            num_variants=request.num_variants, topic=request.topic, niche=request.niche,
            target_audience=request.target_audience, style=request.style.value,
            voice_section=voice, reference_section=refs, cta_instruction=cta)


# --- Main Pipeline ---
class TweetGenerator:
    """Production tweet/thread/reply generation pipeline."""

    def __init__(self, config: GeneratorConfig | None = None):
        self.config = config or GeneratorConfig()

    async def generate(self, request: GenerateTweetRequest) -> GenerateTweetResponse:
        start = time.monotonic()
        self._validate(request)
        prompt = build_prompt(request)
        model = {ContentType.THREAD: self.config.thread_model,
                 ContentType.REPLY: self.config.reply_model}.get(request.content_type, self.config.tweet_model)
        max_tok = {ContentType.THREAD: self.config.max_tokens_thread,
                   ContentType.REPLY: self.config.max_tokens_reply}.get(request.content_type, self.config.max_tokens_tweet)

        raw, tokens = await call_llm(prompt, model, self.config, max_tok,
            "You are a world-class X content strategist. Respond ONLY in valid JSON.")
        parsed = parse_llm_output(raw, request.content_type)

        resp = GenerateTweetResponse(
            request_id=f"gen_{int(time.time()*1000)}", content_type=request.content_type,
            generation_time_ms=round((time.monotonic()-start)*1000, 2),
            model_used=model, tokens_used=tokens)

        if request.content_type == ContentType.THREAD:
            resp.thread = [ThreadTweet(**item) for item in parsed.get("thread", [])]
        else:
            for item in parsed.get("variants", []):
                text = item.get("text", "")
                resp.variants.append(TweetVariant(
                    text=text, hook_type=item.get("hook_type", ""),
                    char_count=len(text), estimated_engagement=item.get("estimated_engagement", ""),
                    reasoning=item.get("reasoning", "")))
        return resp

    def _validate(self, r: GenerateTweetRequest):
        if r.content_type == ContentType.REPLY and not r.original_tweet_text:
            raise ValueError("original_tweet_text required for replies")


if __name__ == "__main__":
    async def demo():
        gen = TweetGenerator()
        result = await gen.generate(GenerateTweetRequest(
            topic="Why most SaaS startups fail in year one",
            style=TweetStyle.PROVOCATIVE, niche="SaaS",
            target_audience="startup founders", num_variants=3))
        for v in result.variants:
            print(f"[{v.hook_type}] {v.text}\n")
    asyncio.run(demo())
